$("#work_tag_submit_btn").click(function(e) {
    if($("#work_tag_input_text").val() == '') {
        e.preventDefault();
    }
});
$("#work_tag_input_text").keypress(function(e) {
    if (event.which == 13 && $("#work_tag_input_text").val() == '') {
        e.preventDefault();
    }
});

$("#current_projects_submit_btn").click(function(e) {
    if($("#current_projects_input_text").val() == '') {
        e.preventDefault();
    }
});
$("#current_projects_input_text").keypress(function(e) {
    if (event.which == 13 && $("#current_projects_input_text").val() == '') {
        e.preventDefault();
    }
});

$("#things_im_good_at_submit_btn").click(function(e) {
    if($("#things_im_good_at_input_text").val() == '') {
        e.preventDefault();
    }
});
$("#things_im_good_at_input_text").keypress(function(e) {
    if (event.which == 13 && $("#things_im_good_at_input_text").val() == '') {
        e.preventDefault();
    }
});

$("#other_things_submit_btn").click(function(e) {
    if($("#other_things_input_text").val() == '') {
        e.preventDefault();
    }
});
$("#other_things_input_text").keypress(function(e) {
    if (event.which == 13 && $("#other_things_input_text").val() == '') {
        e.preventDefault();
    }
});

