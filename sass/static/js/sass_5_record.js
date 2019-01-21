$('#submitBtn').click(function () {
});

$('#submit').click(function () {
    $('#sass-form').submit();
});

$(document).ready(function () {
    if (isUpdate) {
        $("select[name=sic-rating]").val(sicRating.split('_')[1]);
        $("select[name=sooc-rating]").val(soocRating.split('_')[1]);
        $("select[name=bedrock-rating]").val(bedrockRating.split('_')[1]);

        $("select[name=mic-rating]").val(micRating.split('_')[1]);
        $("select[name=mooc-rating]").val(moocRating.split('_')[1]);
        $("select[name=aquatic-veg-rating]").val(aquaticVegRating.split('_')[1]);

        $("select[name=gravel-rating]").val(gravelRating.split('_')[1]);
        $("select[name=sand-rating]").val(sandRating.split('_')[1]);
        $("select[name=mud-rating]").val(mudRating.split('_')[1]);

        $("select[name=hand-picking-rating]").val(handPickingRating.split('_')[1]);

        $('#submitBtn').val('Update');
    }
});