$('#submitBtn').click(function () {
});

$('#submit').click(function () {
    $('#sass-form').submit();
});

$(document).ready(function () {
    if (isUpdate) {
        $("input[name=sic-rating]:checked").val(sicRating.split('_')[1]);
        $("input[name=sooc-rating]:checked").val(soocRating.split('_')[1]);
        $("input[name=bedrock-rating]:checked").val(bedrockRating.split('_')[1]);

        $("input[name=mic-rating]:checked").val(micRating.split('_')[1]);
        $("input[name=mooc-rating]:checked").val(moocRating.split('_')[1]);
        $("input[name=aquatic-veg-rating]:checked").val(aquaticVegRating.split('_')[1]);

        $("input[name=gravel-rating]:checked").val(gravelRating.split('_')[1]);
        $("input[name=sand-rating]:checked").val(sandRating.split('_')[1]);
        $("input[name=mud-rating]:checked").val(mudRating.split('_')[1]);

        $("input[name=hand-picking-rating]:checked").val(handPickingRating.split('_')[1]);

        $('#submitBtn').val('Update');
    }
});