document.addEventListener("DOMContentLoaded", () => {
  const codeInput = document.querySelector('input[name="code"]');
  if (codeInput) {
    codeInput.focus();
    codeInput.addEventListener("input", () => {
      codeInput.value = codeInput.value.replace(/\D/g, "").slice(0, 6);
    });
  }
});