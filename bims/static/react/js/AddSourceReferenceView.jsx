import React from 'react';
import '../css/SourceReference.scss';
import DOI from "./components/DOI";
import Author from "./components/Author";


const PEER_REVIEWED = 'Peer-reviewed scientific article'
const PUBLISHED_REPORT = 'Published report or thesis'
const DATABASE = 'Database'
const REPORT_SOURCE = ['url', 'file']

class AddSourceReferenceView extends React.Component {
  constructor(props){
    super(props);
    this.state = {
      selected_reference_type: DATABASE,
      authors: []
    };
    this.handleChange = this.handleChange.bind(this);
    this.handleSubmit = this.handleSubmit.bind(this);
    this.field = this.field.bind(this);
    this.updateForm = this.updateForm.bind(this);
    this.handleInputChange = this.handleInputChange.bind(this);
    this.handleReportSourceChange = this.handleReportSourceChange.bind(this);
  }

  handleChange(event) {
    this.setState({
      selected_reference_type: event.target.value,
      name: '',
      source: '',
      description: '',
      url: '',
      year: '',
      report_source: REPORT_SOURCE[1],
      authors: []
    });
  }

  handleSubmit(event) {
    event.preventDefault();
    event.submit();
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

  handleReportSourceChange(event) {
    this.setState({
      report_source: event.target.value
    });
  }

  field(field) {
    switch (field) {
      case 'doi':
        return this.state.selected_reference_type === PEER_REVIEWED
      case 'author':
      case 'year':
        return this.state.selected_reference_type === PEER_REVIEWED || this.state.selected_reference_type === PUBLISHED_REPORT
      case 'file':
        return this.state.selected_reference_type === PUBLISHED_REPORT
      case 'description':
      case 'url':
        return this.state.selected_reference_type === DATABASE
      default:
        return false
    }
  }

  updateForm(formData) {
    this.setState(formData)
  }

  render() {
    return (
      <form encType="multipart/form-data" name="source_reference_form" method="post">
        <input type="hidden" name="csrfmiddlewaretoken" value={this.props.csrfToken} />
        <div className="form-group">
          <label>Type</label>
          <select name="reference_type" className="form-control" value={this.state.selected_reference_type} onChange={this.handleChange}>
            {this.props.reference_type.map((reference_type) =>
              <option value={reference_type}>{ reference_type }</option>
            )}
          </select>
        </div>
        {/*DOI*/}
        {this.field('doi') ?
          <DOI updateForm={this.updateForm} /> : null
        }
        {
          this.field('file') ?
            <div>
              <div className="form-check">
                <input className="form-check-input" type="radio"
                       name="reportSourceRadios" id="provide-url" value="url" checked={this.state.report_source === 'url'}
                       onChange={(e) => this.handleReportSourceChange(e)} />
                  <label className="form-check-label" htmlFor="provide-url">
                    Provide url
                  </label>
              </div>
              <div className="form-check">
                <input className="form-check-input" type="radio"
                       name="reportSourceRadios" id="upload-file" value="file" checked={this.state.report_source === 'file'}
                       onChange={(e) => this.handleReportSourceChange(e)} />
                  <label className="form-check-label" htmlFor="upload-file">
                    Upload a file
                  </label>
              </div>

              <div className="form-group">
                {this.state.report_source === 'file' ?
                    <input type="file" className="form-control"
                           accept="application/pdf"
                           id="report_file" aria-describedby="fileHelp"/>
                   : <input id="document-url" type="text"
                            placeholder="Enter url"
                            className="form-control form-control-sm" name="report_url"/> }
              </div>

            </div>
          : null
        }
        <div className="form-group required-input">
          <label>Name</label>
          <input type="text" className="form-control"
                 name="name" id="title" aria-describedby="titleHelp" required
                 placeholder="Enter Name" value={this.state.name} onChange={(e) => this.handleInputChange('name', e)}/>
        </div>
        {this.field('source') ?
        <div className="form-group">
          <label>Source</label>
          <input type="text" className="form-control"
                 name="source" id="source" aria-describedby="sourceHelp"
                 placeholder="Enter Source" value={this.state.source}  onChange={(e) => this.handleInputChange('source', e)}/>
        </div> : null }

        {this.field('description') ?
        <div className="form-group">
          <label>Description</label>
          <input type="text" className="form-control"
                 name="description" id="description" aria-describedby="sourceHelp"
                 placeholder="Enter Description" value={this.state.description}  onChange={(e) => this.handleInputChange('description', e)}/>
        </div> : null }

        {this.field('url') ?
        <div className="form-group">
          <label>URL</label>
          <input type="text" className="form-control"
                 name="url" id="url" aria-describedby="urlHelp"
                 placeholder="Enter URL" value={this.state.url}  onChange={(e) => this.handleInputChange('url', e)}/>
        </div> : null }

        {this.field('year') ?
          <div className="form-group">
            <label>Year</label>
            <input type="number" className="form-control" maxLength="4"
                   name="year" id="year" aria-describedby="yearHelp"
                   placeholder="Enter Year"  value={this.state.year} onChange={(e) => this.handleInputChange('year', e)} />
          </div> : null
        }

        { this.field('author') ? <Author authors={this.state.authors}/> : null }
        <button type="submit" className="btn btn-primary">Submit</button>
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
