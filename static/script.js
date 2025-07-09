let chatHistory = [];  // Chat memory
//local ai chat text----------------------------------------------------------------------------------------------------
function sendToBackend() {
  const text = document.getElementById('textInput').value;

  fetch('http://127.0.0.1:8000/talk', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text })
  })
  .then(response => response.json())
  .then(data => {
    const responseBox = document.getElementById('responseBox');
    let message = `<p><strong>Oh, ${data.emotion} vibes detected! Laugh at this:</strong></p>
                   <p>"${data.joke}"</p>`;

    if (data.suggest_doctor) {
      message += `<p style="color: #ff6666;">
                    Feeling overwhelmed? <br>
                    <a href="/doctors" class="custom-btn mt-2 mb-4 d-inline-flex align-items-center">
  <img src="https://img.icons8.com/color/48/000000/google-maps.png" alt="Map Icon" width="24" height="24" style="margin-right: 10px;" />
  Find Nearby Doctors
</a>

                  </p>`;
    }

    responseBox.innerHTML += message;
    responseBox.scrollTop = responseBox.scrollHeight;

    // Speak Joke First
    const jokeUtterance = new SpeechSynthesisUtterance(`Oh, ${data.emotion} vibes detected! Here's a joke: ${data.joke}`);
    speechSynthesis.speak(jokeUtterance);

    // After joke finishes, speak Doctor Suggestion (if needed)
    jokeUtterance.onend = () => {
      if (data.suggest_doctor) {
        const doctorUtterance = new SpeechSynthesisUtterance("You seem overwhelmed. Let me help you find nearby doctors. Click the button and see the list of doctors");
        speechSynthesis.speak(doctorUtterance);
      }
    };
  })
  .catch(err => {
    console.error('Error talking to server:', err);
    alert("Error talking to server. Is your backend running?");
  });
}

//doctor location-------------------------------------------------------------------------------------------------------
let map;   // Global map object
let userMarker;
let doctorMarkers = [];

// ✅ This function auto-called by Google API after load
function initMap() {
  map = new google.maps.Map(document.getElementById('map'), {
    center: { lat: 0, lng: 0 },  // Dummy center, will update later
    zoom: 12
  });

  // Now, fetch actual location after map loads:
  if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(position => {
      const userLat = position.coords.latitude;
      const userLng = position.coords.longitude;

      // Move map to your location
      map.setCenter({ lat: userLat, lng: userLng });

      // Place marker on your location
      userMarker = new google.maps.Marker({
        position: { lat: userLat, lng: userLng },
        map: map,
        title: 'Your Location',
        icon: 'http://maps.google.com/mapfiles/ms/icons/blue-dot.png'
      });
    }, () => {
      alert("Location access denied.");
    });
  } else {
    alert("Geolocation not supported.");
  }
}


// ✅ Find Doctors Function (same as before)
function findNearbyDoctors() {
  if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(position => {
      fetch('http://127.0.0.1:8000/nearby_doctors', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          lat: position.coords.latitude,
          lng: position.coords.longitude
        })
      })
      .then(res => res.json())
      .then(data => {
        const userLat = position.coords.latitude;
        const userLng = position.coords.longitude;

        let doctorDetails = "";
        data.results.forEach(d => {
          const distance = calculateDistance(userLat, userLng, d.geometry.location.lat, d.geometry.location.lng);
          doctorDetails += `${d.name} - ${d.vicinity}\nDistance: ${distance.toFixed(2)} km\n\n`;
        });

        alert("Nearby Doctors with Distance:\n\n" + doctorDetails);

        // ✅ Update Map after Doctor Data Loaded
        updateMap(userLat, userLng, data.results);
      });
    });
  } else {
    alert("Location access not supported.");
  }
}

// ✅ Distance Calculator (Haversine Formula)
function calculateDistance(lat1, lng1, lat2, lng2) {
  const toRad = x => x * Math.PI / 180;
  const R = 6371; // Radius of Earth in km
  const dLat = toRad(lat2 - lat1);
  const dLng = toRad(lng2 - lng1);
  const a = Math.sin(dLat / 2) ** 2 +
            Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) *
            Math.sin(dLng / 2) ** 2;
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return R * c; // in km
}

// ✅ Update Map Function (Centers + Adds Markers with InfoWindows)
function updateMap(userLat, userLng, doctors) {
  // Center map on user location
  map.setCenter({ lat: userLat, lng: userLng });
  map.setZoom(14);

  // Clear previous markers
  if (userMarker) userMarker.setMap(null);
  doctorMarkers.forEach(marker => marker.setMap(null));
  doctorMarkers = [];

  // Add user marker with auto InfoWindow
  userMarker = new google.maps.Marker({
    position: { lat: userLat, lng: userLng },
    map: map,
    title: 'Your Location',
    icon: 'http://maps.google.com/mapfiles/ms/icons/blue-dot.png'
  });

  const userInfoWindow = new google.maps.InfoWindow({
    content: "<strong>Your Location</strong>"
  });
  userInfoWindow.open(map, userMarker);  // Auto-open user label

  // Add doctor markers with clickable InfoWindows
  doctors.forEach(d => {
    const marker = new google.maps.Marker({
      position: { lat: d.geometry.location.lat, lng: d.geometry.location.lng },
      map: map,
      title: d.name
    });
    doctorMarkers.push(marker);

    const infoWindow = new google.maps.InfoWindow({
      content: `<strong>${d.name}</strong><br>${d.vicinity}`
    });

    // Show label on marker click
    marker.addListener('click', () => {
      infoWindow.open(map, marker);
    });
  });
}

//local ai chat speaker-------------------------------------------------------------------------------------------------
function startVoiceInput() {
  if (!('webkitSpeechRecognition' in window)) {
    alert("Sorry, your browser doesn't support speech recognition.");
    return;
  }

  const recognition = new webkitSpeechRecognition();
  recognition.lang = "en-US";
  recognition.interimResults = false;
  recognition.maxAlternatives = 1;

  recognition.start();

  recognition.onresult = function (event) {
    const transcript = event.results[0][0].transcript;
    document.getElementById("textInput").value = transcript;
    sendToBackend(); // For emotion-based joke
  };

  recognition.onerror = function (event) {
    alert("Speech recognition error: " + event.error);
  };
}
//live jokes -----------------------------------------------------------------------------------------------------------
async function getLiveJoke() {
  try {
    const resp = await fetch('http://127.0.0.1:8000/live_joke');
    const data = await resp.json();

    const joke = data.joke;
    const box = document.getElementById('responseBox');
    box.innerHTML += `<p><strong>😂 Live Joke:</strong> ${joke}</p>`;
    speak(joke);
    box.scrollTop = box.scrollHeight;
  } catch (err) {
    console.error("Live joke fetch error:", err);
    alert("Couldn't fetch live joke.");
  }
}
//live news ------------------------------------------------------------------------------------------------------------
async function getLiveNews() {
  try {
    const resp = await fetch('http://127.0.0.1:8000/live_news');
    const data = await resp.json();

    const box = document.getElementById('responseBox');
    let msg = "📰 Latest news:<br>";

    data.articles.slice(0, 5).forEach(a => {
      msg += `• ${a.title}<br>`;
    });

    box.innerHTML += `<p>${msg}</p>`;
    speak(msg.replace(/<br>/g, '. '));
    box.scrollTop = box.scrollHeight;
  } catch (err) {
    console.error("Live news fetch error:", err);
    alert("Couldn't fetch live news.");
  }
}

//mouth of app----------------------------------------------------------------------------------------------------------
function speak(text) {
  if ('speechSynthesis' in window && text.trim() !== "") {
    const cleanedText = text
      .replace(/[\p{Emoji_Presentation}\p{Extended_Pictographic}]/gu, '')
      .replace(/#[^\s#]+/g, '')
      .replace(/\*/g, '')
      .trim();

    const utterance = new SpeechSynthesisUtterance(cleanedText);
    utterance.lang = "en-US";
    utterance.rate = 1;

    window.speechSynthesis.speak(utterance);
  } else {
    alert("Sorry, speech synthesis not supported or text is empty.");
  }
}
//ask funny friend text ------------------------------------------------------------------------------------------------
function askLLMText() {
  const text = document.getElementById("textInput").value.trim();
  if (!text) {
    alert("Please type something to ask the funny assistant!");
    return;
  }
  sendLLMRequest(text);
}
//ask funny friend speak -----------------------------------------------------------------------------------------------
function askLLMSpeak() {
  const recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
  recognition.lang = "en-US";
  recognition.start();

  recognition.onresult = function (event) {
    const spokenText = event.results[0][0].transcript.trim();

    // 🟡 Add this line for debugging
    console.log("Captured voice:", spokenText);

    if (!spokenText) {
      alert("Mic didn't catch anything.");
      return;
    }

    document.getElementById("textInput").value = spokenText;

    // 🔁 Small delay to ensure textInput updates visually
    setTimeout(() => sendLLMRequest(spokenText), 100);
  };

  recognition.onerror = function (event) {
    console.error("Speech error:", event.error);
    alert("Speech recognition error: " + event.error);
  };
}
//funny friend chat history---------------------------------------------------------------------------------------------
function sendLLMRequest(text) {
  const responseBox = document.getElementById("responseBox");

  // Add user message to history
  chatHistory.push({ role: "user", content: text });

  fetch("http://127.0.0.1:8000/llm_chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ messages: chatHistory })
  })
  .then(res => res.json())
  .then(data => {
    // Add assistant reply to history
    chatHistory.push({ role: "assistant", content: data.reply });

    // Show both in chat window
    responseBox.innerHTML += `<p><strong>You:</strong> ${text}</p>`;
    responseBox.innerHTML += `<p><strong>🤖 Funny Friend:</strong> ${data.reply}</p>`;

    speak(data.reply);
    responseBox.scrollTop = responseBox.scrollHeight;
  })
  .catch(err => {
    console.error("LLM chat error:", err);
    alert("Could not reach the funny assistant.");
  });
}

//light bulb control----------------------------------------------------------------------------------------------------
// ✅ Open Smart Control Box (For Any Additional Toggles, Optional)
function openSmartControl() {
  const box = document.getElementById("smartControlBox");
  box.style.display = box.style.display === "none" ? "block" : "none";
}

// ✅ Handle Smart Command (Detect Mobile/Desktop Inputs)
function handleSmartCommand() {
  const desktopInput = document.getElementById("smartCommandDesktop");
  const mobileInput = document.getElementById("smartCommandMobile");

  const text = desktopInput?.value || mobileInput?.value;
  runSmartCommand(text.trim().toLowerCase());
}

// ✅ Send Command to Backend + Animate Devices
function runSmartCommand(text) {
  const box = document.getElementById("responseBox");

  fetch("http://127.0.0.1:8000/device_control", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text: text })
  })
  .then(response => response.json())
  .then(data => {
    if (data.success) {
      const { device, action } = data;

      if (device === "fan") {
        animateFan(action === "on");
        box.innerHTML += `<p>🌀 Fan turned ${action.toUpperCase()}</p>`;
        speak(`Fan is now ${action}`);
      } else if (device === "light") {
        toggleLight(action === "on");
        box.innerHTML += `<p>💡 Light turned ${action.toUpperCase()}</p>`;
        speak(`Light is now ${action}`);
      }
    } else {
      speak("Sorry, I didn't understand.");
      box.innerHTML += `<p>⚠️ Unknown smart command: "${text}"</p>`;
    }

    box.scrollTop = box.scrollHeight;
  })
  .catch(error => {
    console.error("Error:", error);
    speak("Failed to send smart command.");
  });
}

// ✅ Fan Animation (Both Desktop & Mobile Icons)
function animateFan(on) {
  const fanIcons = [
    document.getElementById("fanIconMobile"),
    document.getElementById("fanIconDesktop")
  ];
  fanIcons.forEach(icon => {
    if (icon) icon.classList.toggle("spinning", on);
  });
}

// ✅ Light Toggle (Both Desktop & Mobile Icons)
function toggleLight(on) {
  const lightIcons = [
    document.getElementById("lightIconMobile"),
    document.getElementById("lightIconDesktop")
  ];
  lightIcons.forEach(icon => {
    if (icon) {
      icon.style.color = on ? "#00cc00" : "#666666";
      icon.style.textShadow = on ? "0 0 10px #00cc00" : "none";
    }
  });
}

// ✅ Speak Function (Simple Text-to-Speech)
function speak(text) {
  const utterance = new SpeechSynthesisUtterance(text);
  speechSynthesis.speak(utterance);
}

// ✅ Mic Command with Real Speech Recognition (Web Speech API)
function speakSmartCommand() {
  const recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
  recognition.lang = 'en-US';
  recognition.interimResults = false;
  recognition.maxAlternatives = 1;

  recognition.onresult = function(event) {
    const command = event.results[0][0].transcript;
    console.log("Voice command:", command);
    runSmartCommand(command.toLowerCase());
  };

  recognition.onerror = function(event) {
    console.error("Speech recognition error:", event.error);
    speak("Sorry, I couldn't hear you.");
  };

  recognition.start();
}

//find place by emotion google map--------------------------------------------------------------------------------------
let allPlaces = [];
let currentIndex = 0;
let userLat = 0, userLng = 0;
let detectedEmotion = "";

const emotionCategories = {
  happy: ['amusement_park', 'movie_theater', 'zoo', 'bowling_alley'],
  sad: ['park', 'cafe', 'museum', 'art_gallery'],
  angry: ['gym', 'boxing_gym', 'spa', 'park'],
  stress: ['spa', 'park', 'cafe', 'library'],
  loneliness: ['cafe', 'shopping_mall', 'aquarium', 'church'],
  bored: ['movie_theater', 'shopping_mall', 'bowling_alley', 'amusement_park'],
  romantic: ['restaurant', 'park', 'art_gallery', 'cafe'],
  hungry: ['restaurant', 'cafe', 'bakery', 'food_court'],
  neutral: ['cafe', 'park', 'library', 'museum']
};

function findPlacesByEmotion() {
  const text = document.getElementById("textInput").value;
  if (!text) {
    alert("Please enter some text about your mood or emotion!");
    return;
  }

  fetch('http://127.0.0.1:8000/detect_emotion', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text })
  })
    .then(res => res.json())
    .then(data => {
      detectedEmotion = data.emotion;

      if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(function (position) {
          userLat = position.coords.latitude;
          userLng = position.coords.longitude;

          // Show Category Buttons
          showCategoryButtons(detectedEmotion);

        }, function (error) {
          alert("Location permission denied or unavailable. Please enable location or try again.");
        });
      } else {
        alert("Geolocation is not supported by this browser.");
      }
    });
}

function showCategoryButtons(emotion) {
  let output = `<strong>Emotion Detected:</strong> ${emotion}<br><br>`;
  output += `<strong>Where do you want to go?</strong><br>`;
  const categories = emotionCategories[emotion] || ['cafe', 'park'];

  categories.forEach(placeType => {
    const label = placeType.replace(/_/g, ' ').toUpperCase();
    output += `<button class="custom-btn mt-2 mb-4" onclick="fetchPlaces('${placeType}')">${label}</button> `;
  });

  document.getElementById('responseBox').innerHTML = output;
}

function fetchPlaces(placeType) {
  fetch('http://127.0.0.1:8000/find_places', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ lat: userLat, lng: userLng, place_type: placeType })
  })
    .then(res => res.json())
    .then(places => {
      allPlaces = places.sort((a, b) => a.distance_km - b.distance_km);
      currentIndex = 0;

      // ✅ Save for map page
      localStorage.setItem('placesData', JSON.stringify({
        places: allPlaces,
        userLat,
        userLng,
        placeType
      }));

      showPlaces(placeType);
    });
}

function showPlaces(placeType) {
  let output = `<strong>Places for:</strong> ${placeType.replace(/_/g, ' ').toUpperCase()}<br><br><ul>`;

  const nextPlaces = allPlaces.slice(currentIndex, currentIndex + 5);
  if (nextPlaces.length === 0) {
    output += "<li>No more places found!</li>";
  } else {
    nextPlaces.forEach(place => {
      output += `<li><strong>${place.name}</strong> — ${place.distance_km} km away</li>`;
    });
  }
  output += `</ul>`;

  // ✅ "See on Map" button BELOW places list:
  output += `<button class="custom-btn mt-2 mb-4" onclick="viewPlacesOnMap()">See These Places on Map</button>`;

  // ✅ Load More Button (if more places)
  if (currentIndex + 5 < allPlaces.length) {
    output += `<button class="custom-btn mt-2 mb-4" onclick="loadMorePlaces()">Show More Places</button>`;
  }

  document.getElementById('responseBox').innerHTML = output;

  const speechText = nextPlaces.map(p => `${p.name}, ${p.distance_km} kilometers away`).join('. ');
  speak(speechText);
}

function loadMorePlaces() {
  currentIndex += 5;
  const data = JSON.parse(localStorage.getItem('placesData'));
  showPlaces(data.placeType);
}

function viewPlacesOnMap() {
  window.location.href = "/places_map";
}

