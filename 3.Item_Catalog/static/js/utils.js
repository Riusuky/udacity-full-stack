const ENTER_KEY = 13;

function SetClassModifier(selection, baseClass, modifier) {
    selection.attr('class', selection.attr('class').replace(new RegExp(`${baseClass}[-\\w]*`), baseClass+modifier));
}
