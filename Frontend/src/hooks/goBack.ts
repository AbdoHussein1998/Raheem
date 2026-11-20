/** Return to the previous browser entry, or try closing a directly opened tab. */
export function goBack(): void {
  if (window.history.length > 1) {
    window.history.back();
  } else {
    // Browsers may block closing a tab that was not opened by a script.
    window.close();
  }
}
