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
                                <div class="col-6">${data.rank == 'GENUS' && data.accepted_taxonomy_name ? data.accepted_taxonomy_name : data.genus}</div>
                            </div>
                            <div class="dt-item col-12 row">
                                <div class="col-6"><strong>Subgenus</strong></div>
                                <div class="col-6">${data.rank == 'SUBGENUS' && data.accepted_taxonomy_name ? data.accepted_taxonomy_name : data.subgenus}</div>
                            </div>
                            <div class="dt-item col-12 row">
                                <div class="col-6"><strong>Species group</strong></div>
                                <div class="col-6">${data.species_group}</div>
                            </div>
                            <div class="dt-item col-12 row">
                                <div class="col-6"><strong>Species</strong></div>
                                <div class="col-6">${data.rank == 'SPECIES' && data.accepted_taxonomy_name ? data.accepted_taxonomy_name : data.species}</div>
                            </div>
                            <div class="dt-item col-12 row">
                                <div class="col-6"><strong>Subspecies</strong></div>
                                <div class="col-6">${data.subspecies}</div>
                            </div>
                        </div>
                    </div>
                </div>           
            </div>
            <div class="container container-fluid" style="padding-left:40px;">
                <div class="row">
                    <div class="dt-full-column">
                        <div class="row">
                            <div class="col-12 text-white dt-header">
                                Additional Information
                            </div>
                            <div class="dt-item col-12 row">
                                <div class="col-4"><strong>Taxonomic Comments</strong></div>
                                <div class="col-8">${data.additional_data['Taxonomic comments'] || data.additional_data['Taxonomic Comments'] || ''}</div>
                            </div>
                            <div class="dt-item col-12 row">
                                <div class="col-4"><strong>Conservation Comments</strong></div>
                                <div class="col-8">${data.additional_data['Conservation Comments'] || ''}</div>
                            </div>
                            <div class="dt-item col-12 row">
                                <div class="col-4"><strong>Biogeographic Comments</strong></div>
                                <div class="col-8">${data.additional_data['Biogeographic Comments'] || ''}</div>
                            </div>
                            <div class="dt-item col-12 row">
                                <div class="col-4"><strong>Environmental Comments</strong></div>
                                <div class="col-8">${data.additional_data['Environmental Comments'] || ''}</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
`;
    }

    return {
        formatDetailTaxon
    };
})();
