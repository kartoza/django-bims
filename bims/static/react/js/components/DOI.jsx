import React from 'react';
import axios from 'axios';

class DOI extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      entry: null,
      loading: false
    };
    this.searchByDOI = this.searchByDOI.bind(this)
  }

  getEntryByDOI(doi) {
      const doiUrl = '/bibliography/api/fetch/by-doi/?q=' + doi;
      return new Promise(async (resolve, reject) => await axios.get(doiUrl, {
          timeout: 5000
      }).then(response => {
          resolve(response.data);
      }).catch(function (error) {
          console.log(error)
          reject();
      }))
  }

  searchByDOI(event) {
    const doi = ($('#doi').val());
    this.setState({
      loading: true
    })
    this.getEntryByDOI(doi).then(data => {
      console.log(data);
      this.setState({
        entry: data,
        loading: false
      })
      this.props.updateForm({
        'title': data.title,
        'source': data.journal.name,
        'year': data.publication_date,
        'authors': data.authors
      })
    }).catch(error =>{
       this.setState({
         entry: null,
         loading: false
      })
      this.props.updateForm({
        'title': '',
        'source': '',
        'year': '',
        'authors': []
      })
    })
  }

  render() {
    return (
        <div className="form-group">
          <label>DOI</label>
          <input type="text" className="form-control"
                 id="doi" aria-describedby="emailHelp"
                 placeholder="Enter DOI" />
          <button className="btn btn-primary" onClick={this.searchByDOI} disabled={this.state.loading}>Search by DOI</button>
          { this.state.entry ? (
              this.state.entry.data_exist ? <p>Data already exists</p> : null
          ) : null }
        </div>
    )
  }
}

export default DOI;
