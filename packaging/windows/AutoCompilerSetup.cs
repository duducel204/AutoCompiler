using System;
using System.Diagnostics;
using System.IO;
using System.IO.Compression;
using System.Reflection;
using System.Text;
using System.Windows.Forms;

internal static class AutoCompilerSetup
{
    private const string PayloadResource = "AutoCompiler.Payload";

    [STAThread]
    private static int Main(string[] args)
    {
        string staging = Path.Combine(Path.GetTempPath(), "AutoCompilerSetup-" + Guid.NewGuid().ToString("N"));
        bool uninstall = false;
        string installRoot = Path.Combine(
            Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
            "AutoCompiler"
        );

        try
        {
            Directory.CreateDirectory(staging);
            ExtractPayload(staging);

            string bootstrap = Path.Combine(staging, "bootstrap.ps1");
            if (!File.Exists(bootstrap))
                throw new FileNotFoundException("bootstrap.ps1 is missing from the embedded payload.");

            string psArgs = "-NoProfile -ExecutionPolicy Bypass -File " + Quote(bootstrap)
                + " -PayloadRoot " + Quote(staging);

            for (int i = 0; i < args.Length; i++)
            {
                string arg = args[i];
                if (String.Equals(arg, "--no-launch", StringComparison.OrdinalIgnoreCase))
                {
                    psArgs += " -NoLaunch";
                }
                else if (String.Equals(arg, "--no-shortcuts", StringComparison.OrdinalIgnoreCase))
                {
                    psArgs += " -NoShortcuts";
                }
                else if (String.Equals(arg, "--uninstall", StringComparison.OrdinalIgnoreCase))
                {
                    uninstall = true;
                    psArgs += " -Uninstall";
                }
                else if (String.Equals(arg, "--install-root", StringComparison.OrdinalIgnoreCase) && i + 1 < args.Length)
                {
                    installRoot = Path.GetFullPath(args[++i]);
                    psArgs += " -InstallRoot " + Quote(installRoot);
                }
                else
                {
                    throw new ArgumentException("Unsupported setup argument: " + arg);
                }
            }

            ProcessStartInfo info = new ProcessStartInfo
            {
                FileName = "powershell.exe",
                Arguments = psArgs,
                UseShellExecute = false,
                CreateNoWindow = false
            };
            info.EnvironmentVariables["AUTOCOMPILER_SETUP_SOURCE"] = Assembly.GetExecutingAssembly().Location;

            using (Process process = Process.Start(info))
            {
                process.WaitForExit();
                if (process.ExitCode != 0)
                    throw new InvalidOperationException("Installation bootstrap failed with exit code " + process.ExitCode + ".");
            }

            if (uninstall)
                ScheduleInstallRootRemoval(installRoot);

            return 0;
        }
        catch (Exception ex)
        {
            string log = Path.Combine(Path.GetTempPath(), "AutoCompilerSetup-error.log");
            try
            {
                File.WriteAllText(log, ex.ToString(), Encoding.UTF8);
            }
            catch { }

            MessageBox.Show(
                "AutoCompiler setup failed.\n\n" + ex.Message + "\n\nDetails: " + log,
                "AutoCompiler Setup",
                MessageBoxButtons.OK,
                MessageBoxIcon.Error
            );
            return 1;
        }
        finally
        {
            try
            {
                if (Directory.Exists(staging))
                    Directory.Delete(staging, true);
            }
            catch { }
        }
    }

    private static void ScheduleInstallRootRemoval(string installRoot)
    {
        string command =
            "/c ping 127.0.0.1 -n 3 >nul & rmdir /s /q " + QuoteForCmd(installRoot);

        ProcessStartInfo cleanup = new ProcessStartInfo
        {
            FileName = "cmd.exe",
            Arguments = command,
            UseShellExecute = false,
            CreateNoWindow = true
        };
        Process.Start(cleanup);
    }

    private static void ExtractPayload(string destination)
    {
        Assembly assembly = Assembly.GetExecutingAssembly();
        using (Stream stream = assembly.GetManifestResourceStream(PayloadResource))
        {
            if (stream == null)
                throw new InvalidOperationException("Embedded AutoCompiler payload was not found.");

            using (ZipArchive archive = new ZipArchive(stream, ZipArchiveMode.Read, false))
            {
                string root = Path.GetFullPath(destination) + Path.DirectorySeparatorChar;
                foreach (ZipArchiveEntry entry in archive.Entries)
                {
                    string target = Path.GetFullPath(Path.Combine(destination, entry.FullName));
                    if (!target.StartsWith(root, StringComparison.OrdinalIgnoreCase))
                        throw new InvalidDataException("Unsafe path in embedded payload: " + entry.FullName);

                    if (String.IsNullOrEmpty(entry.Name))
                    {
                        Directory.CreateDirectory(target);
                        continue;
                    }

                    string parent = Path.GetDirectoryName(target);
                    if (!String.IsNullOrEmpty(parent))
                        Directory.CreateDirectory(parent);

                    using (Stream input = entry.Open())
                    using (FileStream output = new FileStream(target, FileMode.Create, FileAccess.Write, FileShare.None))
                    {
                        input.CopyTo(output);
                    }
                }
            }
        }
    }

    private static string Quote(string value)
    {
        return "\"" + value.Replace("\"", "\"\"") + "\"";
    }

    private static string QuoteForCmd(string value)
    {
        return "\"" + value.Replace("\"", "\"\"") + "\"";
    }
}
