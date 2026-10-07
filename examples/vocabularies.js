// Prints the number of allowed values per field. No API key needed.
const C = require('../node');
C.vocabularies().then((v) => {
  console.log('vocab version', v.vocab_version);
  for (const [name, values] of Object.entries(v.fields || {})) {
    console.log(name, Array.isArray(values) ? values.length : Object.keys(values).length);
  }
});
