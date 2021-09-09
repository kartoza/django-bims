import React from 'react';
import '../css/SourceReference.scss';
import DOI from "./components/DOI";
import Author from "./components/Author";


const PEER_REVIEWED = 'Peer-reviewed scientific article'
const PUBLISHED_REPORT = 'Published report or thesis'

class AddSourceReferenceView extends React.Component {
  constructor(props){
    super(props);
    this.state = {
      selected_reference_type: PEER_REVIEWED,
      authors: []
    };
    this.handleChange = this.handleChange.bind(this);
    this.handleSubmit = this.handleSubmit.bind(this);
    this.fieldAllowed = this.fieldAllowed.bind(this);
    this.updateForm = this.updateForm.bind(this);
    this.handleInputChange = this.handleInputChange.bind(this)
  }

  handleChange(event) {
    this.setState({
      selected_reference_type: event.target.value,
      title: '',
      source: '',
      year: '',
      authors: []
    });
  }

  handleSubmit(event) {
    event.preventDefault();
  }

  handleInputChange(field, event) {
    let { value, maxLength } = event.target;
    if (maxLength > 0) {
       value = value.slice(0, maxLength);
    }
    this.setState({
      [field]: value
    })
  }

  fieldAllowed(field) {
    switch (field) {
      case 'doi':
        return this.state.selected_reference_type === PEER_REVIEWED
      case 'author':
      case 'year':
        return this.state.selected_reference_type === PEER_REVIEWED || this.state.selected_reference_type === PUBLISHED_REPORT
      case 'file':
        return this.state.selected_reference_type === PUBLISHED_REPORT
      default:
        return false
    }
  }

  updateForm(formData) {
    this.setState(formData)
  }

  render() {
    return (
      <form onSubmit={this.handleSubmit}>
        <div className="form-group">
          <label>Type</label>
          <select className="form-control" value={this.state.selected_reference_type} onChange={this.handleChange}>
            {this.props.reference_type.map((reference_type) =>
              <option value={reference_type}>{ reference_type }</option>
            )}
          </select>
        </div>
        {/*DOI*/}
        {this.fieldAllowed('doi') ?
          <DOI updateForm={this.updateForm} /> : null
        }
        {this.fieldAllowed('file') ?
          <div className="form-group">
            <label>Upload File</label>
            <input type="file" className="form-control"
                   id="file" aria-describedby="fileHelp"/>
          </div> : null
        }
        <div className="form-group">
          <label>Title</label>
          <input type="text" className="form-control"
                 id="title" aria-describedby="titleHelp"
                 placeholder="Enter Title" value={this.state.title} onChange={(e) => this.handleInputChange('title', e)}/>
        </div>
        <div className="form-group">
          <label>Source</label>
          <input type="text" className="form-control"
                 id="source" aria-describedby="sourceHelp"
                 placeholder="Enter Source" value={this.state.source}  onChange={(e) => this.handleInputChange('source', e)}/>
        </div>
        {this.fieldAllowed('year') ?
          <div className="form-group">
            <label>Year</label>
            <input type="number" className="form-control" maxLength="4"
                   id="year" aria-describedby="yearHelp"
                   placeholder="Enter Year"  value={this.state.year} onChange={(e) => this.handleInputChange('year', e)} />
          </div> : null
        }
        { this.fieldAllowed('author') ? <Author authors={this.state.authors}/> : null }
        <button type="submit" className="btn btn-primary" disabled>Submit</button>
      </form>
    );
  }
}

$(function (){
  $("[data-addsourcereferenceview]").each(function(){
      let props = $(this).data()
      props.history = history;
      delete(props.addsourcereferenceview);
      window.ReactDOM.render(<AddSourceReferenceView {...props}/>, $(this).get(0));
  });
})

export default AddSourceReferenceView;
