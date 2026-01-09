(function() {
    function toggleUploadUI() {
        var val = $('#id_upload_type').val();
        var isSpatial = (val === 'spatial');

        $('#upload-file-wrapper').toggleClass('d-none', val === '');

        $('[data-occurrence-label]').toggleClass('d-none', isSpatial);
        $('[data-spatial-label]').toggleClass('d-none', !isSpatial);

        $('[data-occurrence-hint]').toggleClass('d-none', isSpatial);
        $('[data-spatial-hint]').toggleClass('d-none', !isSpatial);
    }

    function isNonEmpty(v) {
        return !!(v && String(v).trim().length);
    }

    function emailIsValid() {
        var $email = $('#id_email');
        var el = $email[0];
        var val = $email.val();
        if (!isNonEmpty(val)) return false;
        if (el && typeof el.checkValidity === 'function') {
            return el.checkValidity();
        }
        return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(val);
    }

    function hasFileSelected() {
        var el = $('#id_upload_file')[0];
        return !!(el && el.files && el.files.length > 0);
    }

    function recaptchaChecked() {
        let el = $('#recaptcha-token-input');
        if (!window.hasRecaptcha) {
            return true;
        } else {
            return isNonEmpty(el.val());
        }
    }

    function updateSubmitState() {
        var enable = hasFileSelected() && isNonEmpty($('#id_name').val()) && isNonEmpty($('#id_title').val()) && emailIsValid() && recaptchaChecked();
        $('#submit-button').prop('disabled', !enable);
    }

    function setFlash(type, html) {
        var $f = $('#flash-area');
        $f.removeClass('d-none alert-success alert-danger')
            .addClass(type === 'success' ? 'alert-success' : 'alert-danger')
            .html(html);
        if ($f.length) {
            $('html, body').animate({ scrollTop: $f.offset().top - 80 }, 250);
        }
    }

    function clearFieldErrors() {
        $('.form-group').removeClass('has-error');
        $('.help-block.text-danger.dynamic').remove();
    }

    function applyFieldErrors(errors) {
        Object.keys(errors || {}).forEach(function(field) {
            var $field = $('#id_' + field);
            var $group = $field.closest('.form-group');
            if ($group.length) {
                $group.addClass('has-error');
                $('<p class="help-block text-danger dynamic"></p>')
                    .text((errors[field] || []).join(', '))
                    .appendTo($group);
            }
        });
    }

    function submitting(on) {
        var $btn = $('#submit-button');
        if (on) {
            $btn.data('orig-text', $btn.text());
            $btn.text('Submitting...');
            $btn.prop('disabled', true);
        } else {
            $btn.text($btn.data('orig-text') || 'Submit');
            updateSubmitState();
        }
    }

    $('#id_upload_type').on('change', function() {
        toggleUploadUI();
        updateSubmitState();
    });
    $('#id_upload_file').on('change', updateSubmitState);
    $('#id_name, #id_email, #id_title').on('input blur', updateSubmitState);

    $('#upload_form').on('submit', function(e) {
        e.preventDefault();
        clearFieldErrors();
        if ($('#submit-button').prop('disabled')) return;

        var form = this;
        var formData = new FormData(form);
        var csrf = $('input[name="csrfmiddlewaretoken"]').val();

        submitting(true);

        $.ajax({
            url: form.action || window.location.href,
            method: 'POST',
            data: formData,
            processData: false,
            contentType: false,
            cache: false,
            headers: { 'X-CSRFToken': csrf },
            success: function(data) {
                var html = ''
                    + '<strong>Thank you — your upload was received.</strong>'
                    + (data.ticket_number ? ' · Ticket #' + data.ticket_number : '')
                    + (data.issue_url ? ' · <a href="' + data.issue_url + '" target="_blank" rel="noopener">View on GitHub</a>' : '');
                setFlash('success', html);

                $('#id_upload_type').val('');
                $('#id_upload_file').val('');
                $('#id_notes').val('');
                $('#id_title').val('');
                toggleUploadUI();
                updateSubmitState();
            },
            error: function(xhr) {
                try {
                    var payload = xhr.responseJSON || {};
                    if (payload.errors) {
                        applyFieldErrors(payload.errors);
                    }
                    var msg = payload.message || 'Something went wrong while submitting your upload.';
                    setFlash('danger', msg);
                } catch (e) {
                    setFlash('danger', 'Unexpected error occurred.');
                }
            },
            complete: function() {
                submitting(false);
            }
        });
    });

    $(document).ready(function() {
        toggleUploadUI();
        updateSubmitState();
    });
})();