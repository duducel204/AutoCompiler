const HOST = "com.autocompiler.ready_bridge";
const MENU_ID = "autocompiler-send-selection-powershell";

chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: MENU_ID,
    title: "Enviar seleção para PowerShell",
    contexts: ["selection"]
  });
});

chrome.contextMenus.onClicked.addListener((info) => {
  if (info.menuItemId !== MENU_ID || !info.selectionText) return;

  chrome.runtime.sendNativeMessage(
    HOST,
    {
      action: "paste_to_powershell",
      text: info.selectionText
    },
    (response) => {
      if (chrome.runtime.lastError) {
        console.error("AutoCompiler Ready Bridge:", chrome.runtime.lastError.message);
        return;
      }
      console.log("AutoCompiler Ready Bridge:", response);
    }
  );
});
