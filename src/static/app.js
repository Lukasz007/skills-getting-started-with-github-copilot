document.addEventListener("DOMContentLoaded", () => {
  const activitiesList = document.getElementById("activities-list");
  const activitySelect = document.getElementById("activity");
  const signupForm = document.getElementById("signup-form");
  const messageDiv = document.getElementById("message");

  // Function to fetch activities from API
  async function fetchActivities() {
    try {
      const response = await fetch("/activities");
      const activities = await response.json();

      // Clear loading message
      activitiesList.innerHTML = "";

      // Populate activities list
      Object.entries(activities).forEach(([name, details]) => {
        const activityCard = document.createElement("div");
        activityCard.className = "activity-card";

        const spotsLeft = details.max_participants - details.participants.length;

        // Build participants section (bulleted list with remove buttons)
        const participants = Array.isArray(details.participants) ? details.participants : [];
        let participantsHTML = '<div class="participants">';
        participantsHTML += '<h5 class="participants-title">Participants</h5>';
        if (participants.length > 0) {
          participantsHTML += '<ul class="participants-list">';
          participants.forEach((p) => {
            participantsHTML += `
              <li class="participant-item">
                <span class="participant-name">${p}</span>
                <button class="remove-participant" data-email="${p}" aria-label="Remove ${p}">×</button>
              </li>`;
          });
          participantsHTML += '</ul>';
        } else {
          participantsHTML += '<p class="no-participants">No participants yet.</p>';
        }
        participantsHTML += '</div>';

        activityCard.dataset.activity = name;
        activityCard.dataset.max = details.max_participants;
        activityCard.dataset.count = participants.length;

        activityCard.innerHTML = `
          <h4>${name}</h4>
          <p>${details.description}</p>
          <p><strong>Schedule:</strong> ${details.schedule}</p>
          <p class="availability"><strong>Availability:</strong> ${spotsLeft} spots left</p>
          ${participantsHTML}
        `;

        activitiesList.appendChild(activityCard);

        // Add option to select dropdown
        const option = document.createElement("option");
        option.value = name;
        option.textContent = name;
        activitySelect.appendChild(option);
      });
    } catch (error) {
      activitiesList.innerHTML = "<p>Failed to load activities. Please try again later.</p>";
      console.error("Error fetching activities:", error);
    }
  }

  // Handle form submission
  signupForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const email = document.getElementById("email").value;
    const activity = document.getElementById("activity").value;

    try {
      const response = await fetch(
        `/activities/${encodeURIComponent(activity)}/signup?email=${encodeURIComponent(email)}`,
        {
          method: "POST",
        }
      );

      const result = await response.json();

      if (response.ok) {
        messageDiv.textContent = result.message;
        messageDiv.className = "success";
        signupForm.reset();
        // Refresh activities to show updated availability and participants
        activitySelect.innerHTML = '<option value="">-- Select an activity --</option>';
        fetchActivities();
      } else {
        messageDiv.textContent = result.detail || "An error occurred";
        messageDiv.className = "error";
      }

      messageDiv.classList.remove("hidden");

      // Hide message after 5 seconds
      setTimeout(() => {
        messageDiv.classList.add("hidden");
      }, 5000);
    } catch (error) {
      messageDiv.textContent = "Failed to sign up. Please try again.";
      messageDiv.className = "error";
      messageDiv.classList.remove("hidden");
      console.error("Error signing up:", error);
    }
  });

  // Handle participant removal (event delegation)
  activitiesList.addEventListener("click", async (event) => {
    const btn = event.target.closest('.remove-participant');
    if (!btn) return;

    const email = btn.dataset.email;
    // Find the parent activity card to get activity name and dataset
    const activityCard = btn.closest('.activity-card');
    if (!activityCard || !email) return;

    const activity = activityCard.dataset.activity;

    if (!activity) return;

    // Confirm removal
    const confirmRemove = confirm(`Unregister ${email} from ${activity}?`);
    if (!confirmRemove) return;

    try {
      const res = await fetch(
        `/activities/${encodeURIComponent(activity)}/signup?email=${encodeURIComponent(email)}`,
        { method: 'DELETE' }
      );

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        alert(err.detail || 'Failed to remove participant');
        return;
      }

      // Remove participant from DOM
      const li = btn.closest('.participant-item');
      if (li) li.remove();

      // Update dataset count and availability display
      let count = parseInt(activityCard.dataset.count || '0', 10);
      const max = parseInt(activityCard.dataset.max || '0', 10);
      if (!isNaN(count) && count > 0) count = count - 1;
      activityCard.dataset.count = String(count);
      const spotsLeft = max - count;
      const availEl = activityCard.querySelector('.availability');
      if (availEl) {
        availEl.innerHTML = `<strong>Availability:</strong> ${spotsLeft} spots left`;
      }

      // If list becomes empty, show empty state message
      const list = activityCard.querySelector('.participants-list');
      if (!list || list.children.length === 0) {
        const participantsDiv = activityCard.querySelector('.participants');
        if (participantsDiv) {
          participantsDiv.innerHTML = '<h5 class="participants-title">Participants</h5><p class="no-participants">No participants yet.</p>';
        }
      }
    } catch (error) {
      console.error('Error removing participant:', error);
      alert('Failed to remove participant. Please try again.');
    }
  });

  // Initialize app
  fetchActivities();
});
