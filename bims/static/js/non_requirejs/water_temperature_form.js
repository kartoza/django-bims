let alertError = $('.alert-danger');
let alertSuccess = $('.alert-success');
let loading = $('.loading');

const checkStatus = async (taskId) => {
    try {
        const result = await new Promise((resolve, reject) => {
            $.ajax({
                url: `/api/celery-status/${taskId}/?session=upload`,
                headers: {"X-CSRFToken": csrfToken},
                type: 'GET',
                success: resolve,
                error: function(xhr, status, error) {
                    reject(new Error('Error uploading data. ' + error));
                }
            });
        });

        if ((result.state === 'PENDING' || result.state === 'STARTED') && !result['success']) {
            setTimeout(() => checkStatus(taskId), 1000);
        } else {
            loading.hide();
            $('html, body').animate({
                scrollTop: $(".dashboard-title").offset().top
            }, 1);
            document.getElementById('upload').disabled = false;
            document.getElementById('upload').value = 'Upload';
            $('#water_file').val('');

            if (result['success']) {
                alertSuccess.html(result['success']);
                alertSuccess.show();
            } else if (result['error']) {
                alertError.html(result['error']);
                alertError.show();
            }
        }
    } catch (error) {
        // Error callback logic here
        document.getElementById('upload').disabled = false;
        document.getElementById('upload').value = 'Upload';
        alert(error.message);
        loading.hide();
    }
}

const processWaterData = (formData) => {

    alertError.html('');
    alertSuccess.html('');

    alertSuccess.hide();
    alertError.hide();
    $.ajax({
        url: `/upload-water-temperature/`,
        headers: {"X-CSRFToken": csrfToken},
        type: 'POST',
        data: formData,
        contentType: false,
        processData: false,
        success: function (data) {
            if (data['status'] === 'PENDING') {
                checkStatus(data['task']);
            } else {
                alertSuccess.html(data['message']);
                alertSuccess.show();
                document.getElementById('upload').disabled = false;
                document.getElementById('upload').value = 'Upload';
                loading.hide();
                $('html, body').animate({
                    scrollTop: $(".dashboard-title").offset().top
                }, 1);
            }
        }, error: function (xhr, ajaxOptions, thrownError) {
            document.getElementById('upload').disabled = false;
            document.getElementById('upload').value = 'Upload';
            alert('Error uploading data. ' + thrownError);
            loading.hide();
        }
    });
}

$('#upload').click((event) => {

    loading.show();

    let required_inputs = $('input,textarea,select').filter('[required]:visible');
    let isError = false;
    let alertMessage = '';
    $.each(required_inputs, (index, input) => {
        let $input = $(input);
        if (!$input.val()) {
            isError = true;
            $input.addClass('error');
            $input.keyup((e) => {
                let $target = $(e.target);
                if ($target.val()) {
                    $target.removeClass('error');
                    $target.next().hide();
                    $target.unbind();
                }
            });
            $input.next().show();
        } else {
            $input.unbind();
        }
    });
    if (alertMessage) {
        let alertDiv = $('.alert-danger');
        alertDiv.html(alertMessage);
        alertDiv.show();
    }
    if (isError) {
        event.preventDefault();
        event.stopPropagation();
        setTimeout(function () {
            window.scrollTo(0, 0);
        }, 500);
        loading.hide();
        return;
    }

    const formData = new FormData();
    formData.append("water_file", $('#water_file')[0].files[0])
    formData.append("site-id", $('#site-id').val())
    formData.append("owner_id", $('#owner_id').val())
    formData.append("interval", $('#logging-interval').val())
    formData.append("format", $('#format-date').val())
    formData.append("start_time", $('#start-time').val())
    formData.append("end_time", $('#end-time').val())
    formData.append("source_reference", $('#selected-source-reference-id').val())
    formData.append("site_image", $('#site_image')[0].files[0])
    formData.append("edit", edit);

    if (edit) {
        formData.append("previous_source_reference_id", $('#previous-source-reference-id').val())
        formData.append("site_image_to_delete", typeof $('#id_site_image_delete').val() !== 'undefined' ? $('#id_site_image_delete').val() : '')
        formData.append("year", year);
        formData.append("source_reference_to_remove", $('#delete-source-reference-id').val());
    }

    document.getElementById('upload').disabled = true;
    document.getElementById('upload').value = 'Checking data...';

    $.ajax({
        url: `/validate-water-temperature/`,
        headers: {"X-CSRFToken": csrfToken},
        type: 'POST',
        data: formData,
        contentType: false,
        processData: false,
        success: function (data) {
            if (data['status'] == 'failed') {
                let alertDiv = $('.alert-danger');
                alertDiv.html('Errors : <br>')
                for (let i = 0; i < data['message'].length; i++) {
                    alertDiv.append(`${data['message'][i]}<br>`)
                }
                alertDiv.show();
                document.getElementById('upload').disabled = false;
                document.getElementById('upload').value = 'Upload';
                $('#water_file').val('');
                $('html, body').animate({
                    scrollTop: $(".dashboard-title").offset().top
                }, 1);
                loading.hide();
            }
            if (data['status'] == 'success') {
                document.getElementById('upload').value = 'Processing data...';
                formData.append("upload_session_id", data['upload_session_id']);
                processWaterData(formData);
            }
        }
    });
});
