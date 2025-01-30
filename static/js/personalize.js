document.addEventListener("DOMContentLoaded", function () {
  // Fetch the list of names for autocomplete
  fetch('/static/data/names.json')
    .then(response => response.json())
    .then(data => {
      const namesList = data.names;
      autocomplete(document.getElementById('child-name'), namesList);
    })
    .catch(error => console.error('Error fetching names:', error));

  function autocomplete(inp, arr) {
    var currentFocus;

    inp.addEventListener("input", function () {
      var a, b, i, val = this.value;
      closeAllLists();
      if (!val) {
        validateInput(inp, arr);
        return false;
      }
      currentFocus = -1;
      a = document.createElement("DIV");
      a.setAttribute("id", this.id + "autocomplete-list");
      a.setAttribute("class", "autocomplete-items");
      this.parentNode.appendChild(a);
      var valUpper = val.toUpperCase();

      var exactMatches = [];
      var startsWithMatches = [];
      var containsMatches = [];

      for (i = 0; i < arr.length; i++) {
        var name = arr[i];
        var nameUpper = name.toUpperCase();

        if (nameUpper === valUpper) {
          exactMatches.push(name);
        } else if (nameUpper.startsWith(valUpper)) {
          startsWithMatches.push(name);
        } else if (nameUpper.includes(valUpper)) {
          containsMatches.push(name);
        }
      }

      var suggestionList = exactMatches.concat(startsWithMatches, containsMatches);
      var maxSuggestions = 10;
      suggestionList = suggestionList.slice(0, maxSuggestions);

      suggestionList.forEach(function (suggestion) {
        b = document.createElement("DIV");
        var nameUpper = suggestion.toUpperCase();
        var matchIndex = nameUpper.indexOf(valUpper);
        b.innerHTML = suggestion.substr(0, matchIndex) +
          "<strong>" + suggestion.substr(matchIndex, val.length) + "</strong>" +
          suggestion.substr(matchIndex + val.length);
        b.innerHTML += "<input type='hidden' value='" + suggestion + "'>";
        b.addEventListener("click", function () {
          inp.value = this.getElementsByTagName("input")[0].value;
          closeAllLists();
          validateInput(inp, arr);
        });
        a.appendChild(b);
      });

      validateInput(inp, arr);
    });

    inp.addEventListener("keydown", function (e) {
      var x = document.getElementById(this.id + "autocomplete-list");
      if (x) x = x.getElementsByTagName("div");

      if (e.keyCode === 40) {
        currentFocus++;
        addActive(x);
      } else if (e.keyCode === 38) {
        currentFocus--;
        addActive(x);
      } else if (e.keyCode === 13) {
        e.preventDefault();
        if (currentFocus > -1 && x) {
          x[currentFocus].click();
        }
      }
    });

    function addActive(x) {
      if (!x) return false;
      removeActive(x);
      if (currentFocus >= x.length) currentFocus = 0;
      if (currentFocus < 0) currentFocus = (x.length - 1);
      x[currentFocus].classList.add("autocomplete-active");
    }

    function removeActive(x) {
      for (var i = 0; i < x.length; i++) {
        x[i].classList.remove("autocomplete-active");
      }
    }

    function closeAllLists(elmnt) {
      var x = document.getElementsByClassName("autocomplete-items");
      for (var i = 0; i < x.length; i++) {
        if (elmnt !== x[i] && elmnt !== inp) {
          if (x[i].parentNode) {
            x[i].parentNode.removeChild(x[i]);
          }
        }
      }
    }

    document.addEventListener("click", function (e) {
      closeAllLists(e.target);
    });

    function validateInput(inp, arr) {
      const icon = document.getElementById('name-validation-icon');
      const inputValue = inp.value.trim().toLowerCase();
      const lowerCaseArr = arr.map(name => name.toLowerCase());

      if (inputValue === '') {
        icon.classList.remove('valid', 'invalid');
        icon.innerHTML = '';
      } else if (lowerCaseArr.includes(inputValue)) {
        icon.classList.remove('invalid');
        icon.classList.add('valid');
        icon.innerHTML = '&#10004;';
      } else {
        icon.classList.remove('valid');
        icon.classList.add('invalid');
        icon.innerHTML = '&#10006;';
      }
    }
  }

  // Gender Selection Logic
  const boyButton = document.getElementById('boy');
  const girlButton = document.getElementById('girl');
  const genderInput = document.getElementById('gender-id');
  const boyCharacters = [
    "/static/images/boy_type-i.png",
    "/static/images/boy_type-ii.png",
    "/static/images/boy_type-iii.png",
    "/static/images/boy_type-iv.png",
    "/static/images/boy_type-v.png",
    "/static/images/boy_type-vi.png"
  ];
  const girlCharacters = [
    "/static/images/girl_type-i.png",
    "/static/images/girl_type-ii.png",
    "/static/images/girl_type-iii.png",
    "/static/images/girl_type-iv.png",
    "/static/images/girl_type-v.png",
    "/static/images/girl_type-vi.png"
  ];
  const characterImages = document.querySelectorAll('.character-img');

  function updateCharacterImages(characterArray) {
    characterImages.forEach(function (img, index) {
      img.src = characterArray[index];
    });
  }

  boyButton.addEventListener('click', function () {
    boyButton.classList.add('active');
    girlButton.classList.remove('active');
    genderInput.value = 'Boy';
    updateCharacterImages(boyCharacters);
  });

  girlButton.addEventListener('click', function () {
    girlButton.classList.add('active');
    boyButton.classList.remove('active');
    genderInput.value = 'Girl';
    updateCharacterImages(girlCharacters);
  });

  // Character Selection Logic
  const characterOptions = document.querySelectorAll('.character-option');
  const characterInput = document.getElementById('character-id');

  characterOptions.forEach(function (option) {
    option.addEventListener('click', function () {
      characterOptions.forEach(opt => opt.classList.remove('selected'));
      option.classList.add('selected');
      characterInput.value = option.getAttribute('data-character');
    });
  });

  // Form Submission
  const form = document.getElementById('personalization-form');
  form.addEventListener('submit', function (e) {
    e.preventDefault();

    const childName = document.getElementById('child-name').value.trim();
    const gender = document.getElementById('gender-id').value;
    const character = document.getElementById('character-id').value;

    if (!childName || !gender || !character) {
      alert('Please complete all fields.');
      return;
    }

    const params = new URLSearchParams({
      child_name: childName,
      gender: gender,
      character: character
    });

    window.location.href = '/preview?' + params.toString();
  });

  // ==========================================
  // NEW: Trigger server-side caching + update
  // the footer when done.
  // ==========================================
  const cachingStatusEl = document.getElementById('caching-status');
  fetch('/init-cache')
    .then(response => response.json())
    .then(data => {
      // data = { is_cached: true, total_images: 48, time_seconds: 1.42, ... }
      if (data.is_cached) {
        cachingStatusEl.innerText = `Caching done! ${data.total_images} images loaded in ${data.time_seconds}s.`;
      }
    })
    .catch(err => {
      console.warn('Caching error:', err);
    });
});
