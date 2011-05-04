
// set the focus to the first non hidden and non disabled form element.

function setFocus() {
    if (document.forms[0]) {
        for (i = 0; i < document.forms[0].elements.length; i++) {
            if (document.forms[0].elements[i].type != "hidden" &&
                document.forms[0].elements[i].disabled != true) {

                document.forms[0].elements[i].focus();
                return;
            }
        }
    }	
}
