(() => {
  const selector = "[data-bold-phrase]";

  const applySourceBold = (element) => {
    if (element.querySelector("strong[data-source-bold]")) return;

    const phrase = element.dataset.boldPhrase;
    const text = element.textContent;
    const occurrence = Number(element.dataset.boldOccurrence || "1");
    let start = -1;
    let searchFrom = 0;
    for (let index = 0; index < occurrence; index += 1) {
      start = text.indexOf(phrase, searchFrom);
      if (start < 0) return;
      searchFrom = start + phrase.length;
    }

    const strong = document.createElement("strong");
    strong.dataset.sourceBold = "true";
    strong.textContent = phrase;
    element.replaceChildren(
      document.createTextNode(text.slice(0, start)),
      strong,
      document.createTextNode(text.slice(start + phrase.length)),
    );
  };

  const applyAllSourceBold = () => {
    document.querySelectorAll(selector).forEach(applySourceBold);
  };

  const observer = new MutationObserver(() => {
    observer.disconnect();
    applyAllSourceBold();
    observer.observe(document.body, {
      childList: true,
      subtree: true,
      characterData: true,
    });
  });

  applyAllSourceBold();
  observer.observe(document.body, {
    childList: true,
    subtree: true,
    characterData: true,
  });
})();
