(() => {
  const seenTextIds = new Set();

  document.querySelectorAll("[data-id]").forEach((element) => {
    const textId = element.dataset.id;
    if (!seenTextIds.has(textId)) {
      seenTextIds.add(textId);
      return;
    }

    // Keep repeated visual content, but expose each localized item to the
    // read-aloud runtime only once.
    element.removeAttribute("data-id");
  });
})();
