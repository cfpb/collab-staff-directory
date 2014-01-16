$("#submit_btn").click(function(e) {
    $("#submit_form").ajaxSubmit(submitOptions);
});

$("#person_name").keypress(function(event) {
    if (event.which == 13) {
        event.preventDefault();
        $("#submit_form").ajaxSubmit(submitOptions);
    }
});

$(".person_autocomplete").autocomplete({
    source: "{% url "search:persons_json" %}",
    select: function(event, ui) {
        $("#person_name").attr("value", ui.item.label);
        $("#person_stub").attr("value", ui.item.stub);
    }
});

var hiddenInput = $('#tag_slugs');

if (hiddenInput.val() == undefined) {
    var tagsList = [];
} else {
    var tagsList = hiddenInput.val().split('/');
}
var i = 0;
for (i = 0; i < tagsList.length; i++) {
    $('#' + tagsList[i]).addClass('pushed');
}

$('.tag_name').click(function(e) {
    var btnClicked = $(this);
    var tagSlugSelected = btnClicked.attr('id');
    if(hiddenInput.val() == "") {
        hiddenInput.val(tagSlugSelected);
    } else {
        // determine if we need to remove this tag
        if(btnClicked.hasClass('pushed')) {
            // remove this tag
            var inputList = hiddenInput.val().split('/');
            var tempStr = "";
            for (i = 0; i < inputList.length; i++) {
                if (inputList[i] != btnClicked.attr('id')) {
                    tempStr += inputList[i] + '/';
                }
                hiddenInput.val(tempStr);
            }
        } else {
            // add tag to list
            hiddenInput.val(hiddenInput.val() + '/' + tagSlugSelected);
        }
    }
});

