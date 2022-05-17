function showDownloadPopup(resource_type, resource_name, callback, site_id = null, survey_id = null, taxon_id  = null) {
  const $downloadPopup = $('#download-popup');
  $downloadPopup.modal('show');

  const $submitDownloadPopup = $downloadPopup.find('.submit-download');
  const $downloadPurpose = $('#download-purpose');

  $submitDownloadPopup.on('click', function () {
    let postData = {
      purpose: $downloadPurpose.val(),
      dashboard_url: window.location.href,
      resource_type: resource_type,
      resource_name: resource_name,
      site_id: site_id,
      survey_id: survey_id,
      taxon_id: taxon_id
    };
    console.log(postData);

    callback();
    $downloadPopup.modal('hide');
  });

  // Remove events
  $downloadPopup.on('hidden.bs.modal', function () {
    $submitDownloadPopup.off('click');
    $downloadPopup.off('hidden.bs.modal')
  })
}
