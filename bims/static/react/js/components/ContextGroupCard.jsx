import React from "react";

export const ContextGroupCard = ({ group, onClick }) => (
    <div className="card" onClick={() => onClick(group)}>
        <div className="card-body">
            <h5 className="card-title">{group.name}</h5>
            {
                !group.is_native_layer ? (
                    <div>GeoContext Group : {group.geocontext_group_key}</div>
                ) : (
                    <div>Layer : {group.native_layer_name}</div>
                )
            }

            <div style={{position: 'absolute', right: 0, top: 0, marginRight: 5}}>
                {group.active ?
                    <span class="badge badge-success">Active</span> :
                    <span class="badge badge-danger">Inactive</span>
                }
            </div>
        </div>
    </div>
);