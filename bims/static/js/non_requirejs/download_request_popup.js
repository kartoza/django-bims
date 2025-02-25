function isInt(value) {
  return !isNaN(value) && (function(x) { return (x | 0) === x; })(parseFloat(value))
}

function showDownloadPopup(resource_type, resource_name, callback, auto_approved = true, on_hidden = null, data_format_dropdown = true) {
  const $downloadPopup = $('#download-popup');
  if(resource_type === 'CSV'){
    $downloadPopup.find('#data-format').show()
    $downloadPopup.find('#data-format-pdf').hide()
  } else if (resource_type === 'PDF') {
    $downloadPopup.find('#data-format').hide()
    $downloadPopup.find('#data-format-pdf').show()
  } else {
    $downloadPopup.find('#data-format').hide()
    $downloadPopup.find('#data-format-pdf').hide()
  }

  if (!data_format_dropdown) {
    $downloadPopup.find('#data-format').hide()
    $downloadPopup.find('#data-format-pdf').hide()
  }

  $downloadPopup.find('#download-popup-title').html(resource_name);
  $downloadPopup.modal('show');
  $('#download-notes').val('');

  const $submitDownloadPopup = $downloadPopup.find('.submit-download');
  const $downloadPurpose = $('#download-purpose');
  const url = '/api/download-request/';

  let urlParams = new URLSearchParams(window.location.href.replace('/taxon', '/&taxon'))
  let taxon_id = isInt(urlParams.get('taxon')) ? urlParams.get('taxon') : null;
  let site_id = isInt(urlParams.get('siteId')) ? urlParams.get('siteId') : null;
  let survey_id = urlParams.get('survey');

  $submitDownloadPopup.on('click', function () {
    $submitDownloadPopup.prop('disabled', true);
    if (data_format_dropdown) {
      if (resource_type === 'CSV') {
        resource_type = $('#download-format').val()
      }
      if (resource_type === 'PDF') {
        resource_type = $('#download-format-pdf').val()
      }
    }
    let postData = {
      purpose: $downloadPurpose.val(),
      dashboard_url: window.location.href,
      resource_type: resource_type,
      resource_name: resource_name,
      site_id: site_id,
      survey_id: survey_id,
      taxon_id: taxon_id,
      notes: $('#download-notes').val(),
      auto_approved: auto_approved ? 'True' : 'False',
    };

    $.ajax({
      url: url,
      headers: {"X-CSRFToken": csrfmiddlewaretoken},
      type: 'POST',
      data: postData,
      success: function (data) {
        callback(data['download_request_id']);
        setTimeout(function () {
          $downloadPopup.modal('hide');
          $submitDownloadPopup.prop('disabled', false);
        }, 500)
      }, error: function (jqXHR, textStatus, errorThrown) {
        let errorMessage = "Error submitting download request.";
        if (jqXHR.responseJSON && jqXHR.responseJSON.error) {
          errorMessage += " " + jqXHR.responseJSON.error;
        } else if (textStatus) {
          errorMessage += " " + textStatus;
        }
        alert(errorMessage);
        $downloadPopup.modal('hide');
        $submitDownloadPopup.prop('disabled', false);
      }
    });
  });

  // Remove events
  $downloadPopup.on('hidden.bs.modal', function () {
    $submitDownloadPopup.off('click');
    $downloadPopup.off('hidden.bs.modal');
    if (on_hidden) {
      on_hidden();
    }
  })
}
