import React from "react";

export const ContextGroupCard = ({ group, onClick }) => (
    <div className="card" onClick={() => onClick(group)}>
        <div className="card-body">
            <h5 className="card-title">{group.name}</h5>
            <div style={{position: 'absolute', right: 0, top: 0, marginRight: 5}}>
                {group.active ?
                    <span class="badge badge-success">Active</span> :
                    <span class="badge badge-danger">Inactive</span>
                }
            </div>
        </div>
    </div>
);