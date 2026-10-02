# Browser selection → PowerShell Ready Automation

Status: **validation / packaging pending**

Purpose:

```text
select text in Edge/Chrome
→ right click
→ "Enviar seleção para PowerShell"
→ Native Messaging host
→ text copied to Windows clipboard
→ existing PowerShell/Windows Terminal window receives Ctrl+V
→ NO Enter key is sent
→ selected web text is not executed automatically
```

The browser extension is Manifest V3 and uses `contextMenus` + `nativeMessaging`.

The native host source is `src/autocompiler/ready_bridge.py`. Product packaging must turn that host into an executable path accepted by the browser, materialize `native-host-manifest.template.json`, insert the final extension ID, and register the manifest for Edge/Chrome at user scope.

This automation must not be marked product-ready until the installer proves:

1. extension installed/enabled;
2. native host executable installed;
3. native-host manifest registered;
4. browser can call the host;
5. an open PowerShell/Windows Terminal window receives the selected text;
6. text is inserted without automatic execution;
7. uninstall removes AutoCompiler-owned registration without changing unrelated browser configuration.
