const handleFileUpload = (event) => {
  const file = event.target.files[0];
  if (!file) {
    console.error('Aucun fichier sélectionné');
    return;
  }

  const formData = new FormData();
  formData.append('file', file);

  console.log('Fichier à envoyer :', file); // Debugging

  const xhr = new XMLHttpRequest();
  xhr.open('POST', `${backendUrl}/upload`, true);

  xhr.upload.onprogress = (event) => {
    if (event.lengthComputable) {
      const percent = Math.round((event.loaded / event.total) * 100);
      setProgress(percent);
    }
  };

  xhr.onload = () => {
    console.log('Réponse backend :', xhr.responseText); // Debugging
    if (xhr.status === 201) {
      console.log('Upload réussi');
    } else {
      console.error('Erreur lors de l\'upload :', xhr.status, xhr.statusText);
    }
    setProgress(0);
  };

  xhr.onerror = () => {
    console.error('Erreur réseau lors de l\'upload');
    setProgress(0);
  };

  xhr.setRequestHeader('Accept', 'application/json'); // Assurez la compatibilité CORS
  xhr.send(formData);
};
