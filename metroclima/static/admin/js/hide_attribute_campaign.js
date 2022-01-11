window.addEventListener("load", function() {
    (function() {
        show_place=false;
        django.jQuery(document).ready(function(){
            if (django.jQuery('#id_mobile_campaign').is(':checked')) {
                django.jQuery(".form-row.field-place").show();
                show_place=true;
            } else {
                django.jQuery(".form-row.field-place").hide();
                show_place=false;
            }
            django.jQuery("#id_mobile_campaign").click(function(){
                show_place=!show_place;
                if (show_place) {
                    django.jQuery(".form-row.field-place").show();
                } else {
                    django.jQuery(".form-row.field-place").hide();
                }
            })
        })
    })(django.jQuery);
});