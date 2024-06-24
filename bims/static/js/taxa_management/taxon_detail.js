export const taxonDetail = (() => {

    function formatDetailTaxon(data) {
        return `
            <div class="container container-fluid" style="padding-left:40px;">
                <div class="row mb-2">
                    <div class="dt-column">
                        <div class="row">
                            <div class="col-12 text-white dt-header">
                                Supra-generic Information
                            </div>
                            <div class="dt-item col-12 row">
                                <div class="col-4"><strong>Kingdom</strong></div> 
                                <div class="col-6">${data.kingdom}</div>
                            </div>
                            <div class="dt-item col-12 row">
                                <div class="col-4"><strong>Phylum</strong></div>
                                <div class="col-6">${data.phylum}</div>
                            </div>
                            <div class="dt-item col-12 row">
                                <div class="col-4"><strong>Class</strong></div>
                                <div class="col-6">${data.class_name}</div>
                            </div>
                            <div class="dt-item col-12 row">
                                <div class="col-4"><strong>Order</strong></div>
                                <div class="col-6">${data.order}</div>
                            </div>
                            <div class="dt-item col-12 row">
                                <div class="col-4"><strong>Family</strong></div>
                                <div class="col-6">${data.family}</div>
                            </div>
                        </div>
                    </div>
                    <div class="dt-column">
                        <div class="row">
                            <div class="col-12 text-white dt-header">
                                Infra Categories
                            </div>
                            <div class="dt-item col-12 row">
                                <div class="col-6"><strong>Subfamily</strong></div>
                                <div class="col-6">${data.subfamily}</div>
                            </div>
                            <div class="dt-item col-12 row">
                                <div class="col-6"><strong>Tribe</strong></div>
                                <div class="col-6">${data.tribe}</div>
                            </div>
                            <div class="dt-item col-12 row">
                                <div class="col-6"><strong>Subtribe</strong></div>
                                <div class="col-6">${data.subtribe}</div>
                            </div>
                        </div>
                    </div>
                    <div class="dt-column">
                        <div class="row">
                            <div class="col-12 text-white dt-header">
                                Valid/Accepted Names
                            </div>
                            <div class="dt-item col-12 row">
                                <div class="col-6"><strong>Genus</strong></div>
                                <div class="col-6">${data.genus}</div>
                            </div>
                            <div class="dt-item col-12 row">
                                <div class="col-6"><strong>Subgenus</strong></div>
                                <div class="col-6">${data.subgenus}</div>
                            </div>
                            <div class="dt-item col-12 row">
                                <div class="col-6"><strong>Species group</strong></div>
                                <div class="col-6">${data.species_group}</div>
                            </div>
                            <div class="dt-item col-12 row">
                                <div class="col-6"><strong>Species</strong></div>
                                <div class="col-6">${data.species}</div>
                            </div>
                            <div class="dt-item col-12 row">
                                <div class="col-6"><strong>Subspecies</strong></div>
                                <div class="col-6">${data.subspecies}</div>
                            </div>
                        </div>
                    </div>
                </div>           
            </div>`;
    }

    return {
        formatDetailTaxon
    };
})();
