using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Runtime.InteropServices;
using System.Text;
using System.Web.Script.Serialization;
using System.Windows.Forms;

internal static class AutoCompilerReadyBridge
{
    private const int MaxTextChars = 200000;

    [DllImport("user32.dll")]
    private static extern bool SetForegroundWindow(IntPtr hWnd);

    [STAThread]
    private static int Main(string[] args)
    {
        if (args.Length > 0 && args[0] == "--self-test")
        {
            Console.WriteLine("READY_BRIDGE_OK");
            return 0;
        }

        try
        {
            Dictionary<string, object> message = ReadMessage();
            Dictionary<string, object> response = Handle(message);
            WriteMessage(response);
            return response.ContainsKey("ok") && Convert.ToBoolean(response["ok"]) ? 0 : 1;
        }
        catch (Exception ex)
        {
            WriteMessage(new Dictionary<string, object>
            {
                {"host", "com.autocompiler.ready_bridge"},
                {"ok", false},
                {"status", "bridge_error"},
                {"executed", false},
                {"error", ex.Message}
            });
            return 1;
        }
    }

    private static Dictionary<string, object> Handle(Dictionary<string, object> message)
    {
        string action = message.ContainsKey("action") ? Convert.ToString(message["action"]) : "";
        if (action == "ping")
        {
            return new Dictionary<string, object>
            {
                {"host", "com.autocompiler.ready_bridge"},
                {"ok", true},
                {"status", "ready"},
                {"executed", false}
            };
        }

        if (action != "paste_to_powershell")
        {
            return new Dictionary<string, object>
            {
                {"host", "com.autocompiler.ready_bridge"},
                {"ok", false},
                {"status", "unsupported_action"},
                {"executed", false}
            };
        }

        string text = message.ContainsKey("text") ? Convert.ToString(message["text"]) : "";
        if (String.IsNullOrEmpty(text))
            return Result(false, "empty_text", false);

        if (text.Length > MaxTextChars)
            return Result(false, "text_too_large", false);

        Clipboard.SetText(text);

        IntPtr target = FindPowerShellWindow();
        if (target == IntPtr.Zero)
            return Result(true, "clipboard_only", false);

        if (!SetForegroundWindow(target))
            return Result(true, "clipboard_only", false);

        System.Threading.Thread.Sleep(120);
        SendKeys.SendWait("^v");

        Dictionary<string, object> result = Result(true, "pasted", false);
        result["window"] = target.ToInt64();
        return result;
    }

    private static IntPtr FindPowerShellWindow()
    {
        string[] names = { "powershell", "pwsh", "WindowsTerminal" };
        foreach (string name in names)
        {
            foreach (Process process in Process.GetProcessesByName(name))
            {
                try
                {
                    if (process.MainWindowHandle != IntPtr.Zero)
                        return process.MainWindowHandle;
                }
                catch { }
            }
        }
        return IntPtr.Zero;
    }

    private static Dictionary<string, object> Result(bool ok, string status, bool executed)
    {
        return new Dictionary<string, object>
        {
            {"host", "com.autocompiler.ready_bridge"},
            {"ok", ok},
            {"status", status},
            {"executed", executed}
        };
    }

    private static Dictionary<string, object> ReadMessage()
    {
        Stream input = Console.OpenStandardInput();
        byte[] header = ReadExact(input, 4);
        int length = BitConverter.ToInt32(header, 0);
        if (length <= 0 || length > 8 * 1024 * 1024)
            throw new InvalidDataException("Invalid native message length.");

        byte[] payload = ReadExact(input, length);
        string json = Encoding.UTF8.GetString(payload);
        JavaScriptSerializer serializer = new JavaScriptSerializer();
        return serializer.Deserialize<Dictionary<string, object>>(json);
    }

    private static void WriteMessage(Dictionary<string, object> response)
    {
        JavaScriptSerializer serializer = new JavaScriptSerializer();
        byte[] payload = Encoding.UTF8.GetBytes(serializer.Serialize(response));
        byte[] header = BitConverter.GetBytes(payload.Length);
        Stream output = Console.OpenStandardOutput();
        output.Write(header, 0, header.Length);
        output.Write(payload, 0, payload.Length);
        output.Flush();
    }

    private static byte[] ReadExact(Stream stream, int length)
    {
        byte[] buffer = new byte[length];
        int offset = 0;
        while (offset < length)
        {
            int read = stream.Read(buffer, offset, length - offset);
            if (read <= 0)
                throw new EndOfStreamException();
            offset += read;
        }
        return buffer;
    }
}
