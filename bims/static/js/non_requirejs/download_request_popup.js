function showDownloadPopup(resource_type, resource_name, callback) {
  const $downloadPopup = $('#download-popup');
  $downloadPopup.find('#download-popup-title').html(resource_name);
  $downloadPopup.modal('show');
  $('#download-notes').val('');

  const $submitDownloadPopup = $downloadPopup.find('.submit-download');
  const $downloadPurpose = $('#download-purpose');
  const url = '/api/download-request/';

  let urlParams = new URLSearchParams(window.location.href.replace('/taxon', '/&taxon'))
  let taxon_id = urlParams.get('taxon');
  let site_id = urlParams.get('siteId');
  let survey_id = urlParams.get('survey');

  $submitDownloadPopup.on('click', function () {
    $submitDownloadPopup.prop('disabled', true);
    let postData = {
      purpose: $downloadPurpose.val(),
      dashboard_url: window.location.href,
      resource_type: resource_type,
      resource_name: resource_name,
      site_id: site_id,
      survey_id: survey_id,
      taxon_id: taxon_id,
      notes: $('#download-notes').val()
    };

    $.ajax({
      url: url,
      headers: {"X-CSRFToken": csrfmiddlewaretoken},
      type: 'POST',
      data: postData,
      success: function (data) {
        callback(data['download_request_id']);
        $downloadPopup.modal('hide');
        $submitDownloadPopup.prop('disabled', false);
      }, error: function () {
        alert('Error submitting download request');
        $downloadPopup.modal('hide');
        $submitDownloadPopup.prop('disabled', false);
      }
    });
  });

  // Remove events
  $downloadPopup.on('hidden.bs.modal', function () {
    $submitDownloadPopup.off('click');
    $downloadPopup.off('hidden.bs.modal')
  })
}
