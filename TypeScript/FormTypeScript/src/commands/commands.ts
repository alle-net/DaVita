Office.onReady(() => {
  Office.actions.associate('OpenTaskpane', () => {
    Office.addin?.showAsTaskpane();
  });
});
