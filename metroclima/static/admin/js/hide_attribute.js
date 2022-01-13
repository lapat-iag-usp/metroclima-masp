window.addEventListener("load", function() {
    (function() {
        show_dates=false;
        django.jQuery(document).ready(function(){
            if (django.jQuery('#id_invalid').is(':checked')) {
                django.jQuery(".form-row.field-start_date").show();
                django.jQuery(".form-row.field-end_date").show();
                show_dates=true;
            } else {
                django.jQuery(".form-row.field-start_date").hide();
                django.jQuery(".form-row.field-end_date").hide();
                show_dates=false;
            }
            django.jQuery("#id_invalid").click(function(){
                show_dates=!show_dates;
                if (show_dates) {
                    django.jQuery(".form-row.field-start_date").show();
                    django.jQuery(".form-row.field-end_date").show();
                } else {
                    django.jQuery(".form-row.field-start_date").hide();
                    django.jQuery(".form-row.field-end_date").hide();
                }
            })
        })
    })(django.jQuery);
});
