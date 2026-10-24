(function () {
  "use strict";

  // Mobile navigation toggle
  var toggle = document.querySelector(".nav-toggle");
  var nav = document.getElementById("site-nav");
  if (toggle && nav) {
    toggle.addEventListener("click", function () {
      var open = nav.classList.toggle("open");
      toggle.setAttribute("aria-expanded", open ? "true" : "false");
    });
  }

  // Dismissible alerts
  document.querySelectorAll(".alert-close").forEach(function (btn) {
    btn.addEventListener("click", function () { btn.parentElement.remove(); });
  });

  // Confirm dialogs for destructive forms
  document.querySelectorAll("form[data-confirm]").forEach(function (form) {
    form.addEventListener("submit", function (e) {
      if (!window.confirm(form.dataset.confirm)) { e.preventDefault(); }
    });
  });

  // ----- Booking form -----
  var form = document.getElementById("booking-form");
  if (!form) { return; }

  var doctor = document.getElementById("doctor_id");
  var date = document.getElementById("appointment_date");
  var time = document.getElementById("appointment_time");
  var help = document.getElementById("slot-help");
  var errBox = document.getElementById("form-errors");

  function refreshSlots() {
    if (!doctor.value || !date.value) { return; }
    var url = "/api/slots?doctor_id=" + encodeURIComponent(doctor.value) +
              "&date=" + encodeURIComponent(date.value);
    fetch(url).then(function (r) { return r.json(); }).then(function (data) {
      if (!data.slots) { help.textContent = data.error || "Could not load slots."; return; }
      var free = 0;
      Array.prototype.forEach.call(time.options, function (opt) {
        if (!opt.value) { return; }
        var slot = data.slots.filter(function (s) { return s.time === opt.value; })[0];
        var taken = slot && !slot.available;
        opt.disabled = !!taken;
        var base = opt.textContent.replace(" (booked)", "");
        opt.textContent = taken ? base + " (booked)" : base;
        if (!taken) { free += 1; }
        if (taken && opt.selected) { time.value = ""; }
      });
      help.textContent = free + " slot(s) available on this date.";
    }).catch(function () { help.textContent = "Could not check slot availability right now."; });
  }
  doctor.addEventListener("change", refreshSlots);
  date.addEventListener("change", refreshSlots);
  refreshSlots();

  // Client-side checks (the server validates everything again)
  form.addEventListener("submit", function (e) {
    var errors = [];
    form.querySelectorAll(".invalid").forEach(function (el) { el.classList.remove("invalid"); });
    function bad(id, msg) { errors.push(msg); document.getElementById(id).classList.add("invalid"); }

    var name = document.getElementById("patient_name").value.trim();
    var email = document.getElementById("patient_email").value.trim();
    var phone = document.getElementById("patient_phone").value.replace(/[\s\-()]/g, "").replace(/^\+91/, "");
    var reason = document.getElementById("reason").value.trim();

    if (!/^[A-Za-z][A-Za-z .'\-]{1,99}$/.test(name)) { bad("patient_name", "Enter a valid patient name (letters only)."); }
    if (!/^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$/.test(email)) { bad("patient_email", "Enter a valid email address."); }
    if (!/^[6-9][0-9]{9}$/.test(phone)) { bad("patient_phone", "Enter a valid 10-digit mobile number."); }
    if (!doctor.value) { bad("doctor_id", "Select a doctor."); }
    if (!date.value) { bad("appointment_date", "Choose an appointment date."); }
    else if (date.value < date.min) { bad("appointment_date", "Appointment date cannot be in the past."); }
    if (!time.value) { bad("appointment_time", "Choose a time slot."); }
    if (reason.length < 5) { bad("reason", "Please describe the reason (at least 5 characters)."); }

    if (errors.length) {
      e.preventDefault();
      errBox.hidden = false;
      errBox.innerHTML = "";
      errors.forEach(function (m) {
        var p = document.createElement("div");
        p.textContent = m;
        errBox.appendChild(p);
      });
      errBox.scrollIntoView({ behavior: "smooth", block: "center" });
    } else {
      document.getElementById("submit-btn").disabled = true; // stop double submit
    }
  });
})();
