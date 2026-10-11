# Android bridge

The Android bridge is a permission-aware Termux-side integration layer. It does not grant Android permissions automatically. Current supported actions are listing Downloads and reading a file from Downloads after explicit approval.

Use `#android` to inspect bridge status and `#permissions` / `#allow ID` to manage pending requests.
