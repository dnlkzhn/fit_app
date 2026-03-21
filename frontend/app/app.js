const API_URL = "/api";

const message = document.getElementById("message");
const userInfo = document.getElementById("user-info");
const logoutButton = document.getElementById("logout");
const seedButton = document.getElementById("seed-exercises");
const themeToggle = document.getElementById("theme-toggle");
const exerciseForm = document.getElementById("exercise-form");
const exerciseNameInput = document.getElementById("exercise-name");
const exerciseCategorySelect = document.getElementById("exercise-category");
const exerciseWeightedSelect = document.getElementById("exercise-weighted");
const exerciseIdInput = document.getElementById("exercise-id");
const exerciseCancelButton = document.getElementById("cancel-exercise");

const exerciseSelect = document.getElementById("exercise");
const exerciseList = document.getElementById("exercise-list");
const entriesList = document.getElementById("entries");
const entryForm = document.getElementById("entry-form");
const cancelEditButton = document.getElementById("cancel-edit");
const entryIdInput = document.getElementById("entry-id");
const workoutTitleInput = document.getElementById("workout-title");
const durationInput = document.getElementById("duration");
const repsInput = document.getElementById("reps");
const weightInput = document.getElementById("weight");

let exercises = [];

function getToken() {
    return localStorage.getItem("token");
}

function authHeaders() {
    return {
        "Content-Type": "application/json",
        Authorization: `Bearer ${getToken()}`,
    };
}

function showMessage(text, type = "info") {
    if (!text) {
        message.textContent = "";
        message.className = "alert";
        return;
    }
    message.textContent = text;
    message.className = `alert ${type}`;
}

async function getErrorMessage(response, fallback) {
    try {
        const data = await response.json();
        if (typeof data.detail === "string") {
            return data.detail;
        }
        if (Array.isArray(data.detail)) {
            return data.detail.map((item) => item.msg || "Invalid input").join(", ");
        }
        if (data.detail) {
            return String(data.detail);
        }
    } catch (error) {
        // ignore parsing errors
    }
    return fallback;
}

function applyTheme(mode) {
    if (mode === "dark") {
        document.body.classList.add("theme-dark");
        themeToggle.textContent = "Light";
    } else {
        document.body.classList.remove("theme-dark");
        themeToggle.textContent = "Dark";
    }
}

function saveTheme(mode) {
    localStorage.setItem("theme", mode);
    applyTheme(mode);
}

function requireAuth() {
    if (!getToken()) {
        window.location.href = "login.html";
        return false;
    }
    return true;
}

async function loadMe() {
    const response = await fetch(`${API_URL}/me`, { headers: authHeaders() });
    if (!response.ok) {
        localStorage.removeItem("token");
        window.location.href = "login.html";
        return;
    }
    const user = await response.json();
    userInfo.textContent = `${user.username} (${user.email})`;
}

async function seedExercises() {
    const response = await fetch(`${API_URL}/seed-exercises`, {
        method: "POST",
        headers: authHeaders(),
    });
    if (!response.ok) {
        const errorMessage = await getErrorMessage(response, "Failed to seed exercises");
        showMessage(errorMessage, "error");
        return;
    }
    showMessage("Exercises seeded", "success");
    await loadExercises();
}

async function createExercise(payload) {
    const response = await fetch(`${API_URL}/exercises`, {
        method: "POST",
        headers: authHeaders(),
        body: JSON.stringify(payload),
    });
    if (!response.ok) {
        const errorMessage = await getErrorMessage(response, "Failed to add exercise");
        showMessage(errorMessage, "error");
        return;
    }
    showMessage("Exercise added", "success");
    resetExerciseForm();
    await loadExercises();
}

async function updateExercise(exerciseId, payload) {
    const response = await fetch(`${API_URL}/exercises/${exerciseId}`, {
        method: "PATCH",
        headers: authHeaders(),
        body: JSON.stringify(payload),
    });
    if (!response.ok) {
        const errorMessage = await getErrorMessage(response, "Failed to update exercise");
        showMessage(errorMessage, "error");
        return;
    }
    showMessage("Exercise updated", "success");
    resetExerciseForm();
    await loadExercises();
}

async function deleteExercise(exerciseId) {
    const response = await fetch(`${API_URL}/exercises/${exerciseId}`, {
        method: "DELETE",
        headers: authHeaders(),
    });
    if (!response.ok) {
        const errorMessage = await getErrorMessage(response, "Failed to delete exercise");
        showMessage(errorMessage, "error");
        return;
    }
    showMessage("Exercise deleted", "success");
    await loadExercises();
}

async function loadExercises() {
    const response = await fetch(`${API_URL}/exercises`, { headers: authHeaders() });
    if (!response.ok) {
        const errorMessage = await getErrorMessage(response, "Failed to load exercises");
        showMessage(errorMessage, "error");
        return;
    }
    exercises = await response.json();
    renderExercises();
    renderExerciseOptions();
}

function renderExercises() {
    if (exercises.length === 0) {
        exerciseList.innerHTML = "<p class=\"subtle\">No exercises yet. Click Seed Defaults to add starter exercises.</p>";
        seedButton.style.display = "inline-flex";
        return;
    }
    seedButton.style.display = "none";
    exerciseList.innerHTML = exercises
        .map((exercise) => {
            const weighted = exercise.is_weighted ? "Weighted" : "Bodyweight";
            return `
                <div class="item">
                    <div>
                        <strong>${exercise.name}</strong>
                        <div class="meta">
                            <span class="tag">${exercise.category}</span>
                            <span class="tag">${weighted}</span>
                        </div>
                    </div>
                    <div class="actions">
                        <button class="secondary" onclick="editExercise(${exercise.id})">Edit</button>
                        <button class="danger" onclick="deleteExercise(${exercise.id})">Delete</button>
                    </div>
                </div>
            `;
        })
        .join("");
}

function resetExerciseForm() {
    exerciseIdInput.value = "";
    exerciseForm.reset();
    exerciseWeightedSelect.value = "weighted";
    exerciseCancelButton.style.display = "none";
    exerciseForm.querySelector("button[type='submit']").textContent = "Add Exercise";
}

function ensureCategoryOption(category) {
    if (!category) {
        return;
    }
    const exists = Array.from(exerciseCategorySelect.options).some(
        (option) => option.value === category
    );
    if (!exists) {
        const option = document.createElement("option");
        option.value = category;
        option.textContent = category;
        exerciseCategorySelect.append(option);
    }
}

function renderExerciseOptions() {
    if (exercises.length === 0) {
        exerciseSelect.innerHTML = "<option value=\"\">No exercises</option>";
        exerciseSelect.disabled = true;
        handleExerciseChange();
        return;
    }
    exerciseSelect.disabled = false;
    exerciseSelect.innerHTML = exercises
        .map((exercise) => `<option value="${exercise.id}">${exercise.name}</option>`)
        .join("");
    handleExerciseChange();
}

function handleExerciseChange() {
    const selectedId = Number(exerciseSelect.value);
    const selected = exercises.find((exercise) => exercise.id === selectedId);
    if (!selected) {
        durationInput.disabled = true;
        repsInput.disabled = true;
        weightInput.disabled = true;
        durationInput.value = "";
        repsInput.value = "";
        weightInput.value = "";
        weightInput.placeholder = "Optional";
        return;
    }
    if (selected.is_weighted) {
        durationInput.disabled = true;
        durationInput.value = "";
        durationInput.placeholder = "Not required";
        repsInput.disabled = false;
        repsInput.placeholder = "Required";
        weightInput.disabled = false;
        weightInput.placeholder = "Required for weighted";
    } else {
        repsInput.disabled = true;
        repsInput.value = "";
        repsInput.placeholder = "Not required";
        durationInput.disabled = false;
        durationInput.placeholder = "Required";
        weightInput.disabled = true;
        weightInput.value = "";
        weightInput.placeholder = "Not required";
    }
}

function resetForm() {
    entryIdInput.value = "";
    workoutTitleInput.value = "";
    durationInput.value = "";
    repsInput.value = "";
    weightInput.value = "";
    cancelEditButton.style.display = "none";
    entryForm.querySelector("button[type='submit']").textContent = "Save Entry";
    handleExerciseChange();
}

async function loadEntries() {
    const response = await fetch(`${API_URL}/workout-entries`, { headers: authHeaders() });
    if (!response.ok) {
        const errorMessage = await getErrorMessage(response, "Failed to load entries");
        showMessage(errorMessage, "error");
        return;
    }
    const entries = await response.json();
    renderEntries(entries);
}

function renderEntries(entries) {
    if (entries.length === 0) {
        entriesList.innerHTML = "<p class=\"subtle\">No entries yet.</p>";
        return;
    }
    entriesList.innerHTML = entries
        .map((entry) => {
            const exercise = exercises.find((item) => item.id === entry.exercise_id);
            const exerciseName = exercise ? exercise.name : `Exercise #${entry.exercise_id}`;
            const weighted = exercise && exercise.is_weighted;
            const metric = weighted ? `${entry.reps ?? 0} reps` : `${entry.duration_minutes ?? 0} min`;
            const weight = entry.weight_kg ? `${entry.weight_kg} kg` : "Bodyweight";
            const performed = new Date(entry.performed_at).toLocaleString();
            return `
                <div class="item">
                    <div>
                        <strong>${entry.workout_title}</strong>
                        <div class="meta">${exerciseName} · ${metric} · ${weight} · ${performed}</div>
                    </div>
                    <div class="actions">
                        <button class="secondary" onclick="editEntry(${entry.id})">Edit</button>
                        <button class="danger" onclick="deleteEntry(${entry.id})">Delete</button>
                    </div>
                </div>
            `;
        })
        .join("");
}

async function createEntry(payload) {
    const response = await fetch(`${API_URL}/workout-entries`, {
        method: "POST",
        headers: authHeaders(),
        body: JSON.stringify(payload),
    });
    if (!response.ok) {
        const errorMessage = await getErrorMessage(response, "Failed to save entry");
        showMessage(errorMessage, "error");
        return;
    }
    showMessage("Entry saved", "success");
    resetForm();
    await loadEntries();
}

async function updateEntry(entryId, payload) {
    const response = await fetch(`${API_URL}/workout-entries/${entryId}`, {
        method: "PATCH",
        headers: authHeaders(),
        body: JSON.stringify(payload),
    });
    if (!response.ok) {
        const errorMessage = await getErrorMessage(response, "Failed to update entry");
        showMessage(errorMessage, "error");
        return;
    }
    showMessage("Entry updated", "success");
    resetForm();
    await loadEntries();
}

async function deleteEntry(entryId) {
    const response = await fetch(`${API_URL}/workout-entries/${entryId}`, {
        method: "DELETE",
        headers: authHeaders(),
    });
    if (!response.ok) {
        const errorMessage = await getErrorMessage(response, "Failed to delete entry");
        showMessage(errorMessage, "error");
        return;
    }
    showMessage("Entry deleted", "success");
    await loadEntries();
}

window.editEntry = async function editEntry(entryId) {
    const response = await fetch(`${API_URL}/workout-entries/${entryId}`, { headers: authHeaders() });
    if (!response.ok) {
        const errorMessage = await getErrorMessage(response, "Failed to load entry");
        showMessage(errorMessage, "error");
        return;
    }
    const entry = await response.json();
    entryIdInput.value = entry.id;
    workoutTitleInput.value = entry.workout_title;
    exerciseSelect.value = String(entry.exercise_id);
    durationInput.value = entry.duration_minutes ?? "";
    repsInput.value = entry.reps ?? "";
    weightInput.value = entry.weight_kg ?? "";
    handleExerciseChange();
    cancelEditButton.style.display = "inline-flex";
    entryForm.querySelector("button[type='submit']").textContent = "Update Entry";
};

window.editExercise = function editExercise(exerciseId) {
    const exercise = exercises.find((item) => item.id === exerciseId);
    if (!exercise) {
        showMessage("Exercise not found", "error");
        return;
    }
    exerciseIdInput.value = String(exercise.id);
    exerciseNameInput.value = exercise.name;
    ensureCategoryOption(exercise.category);
    exerciseCategorySelect.value = exercise.category;
    exerciseWeightedSelect.value = exercise.is_weighted ? "weighted" : "bodyweight";
    exerciseCancelButton.style.display = "inline-flex";
    exerciseForm.querySelector("button[type='submit']").textContent = "Update Exercise";
};

entryForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    showMessage("");

    const selectedId = Number(exerciseSelect.value);
    const selected = exercises.find((exercise) => exercise.id === selectedId);
    if (!selected) {
        showMessage("Select an exercise", "error");
        return;
    }

    const workoutTitle = workoutTitleInput.value.trim();
    if (!workoutTitle) {
        showMessage("Workout title is required", "error");
        return;
    }

    const payload = {
        workout_title: workoutTitle,
        exercise_id: selectedId,
    };

    if (selected.is_weighted) {
        if (!repsInput.value || !weightInput.value) {
            showMessage("Reps and weight are required for weighted exercises", "error");
            return;
        }
        payload.reps = Number(repsInput.value);
        payload.weight_kg = Number(weightInput.value);
    } else {
        if (!durationInput.value) {
            showMessage("Duration is required for non-weighted exercises", "error");
            return;
        }
        payload.duration_minutes = Number(durationInput.value);
    }

    const entryId = entryIdInput.value;
    if (entryId) {
        await updateEntry(entryId, payload);
    } else {
        await createEntry(payload);
    }
});

exerciseSelect.addEventListener("change", handleExerciseChange);

cancelEditButton.addEventListener("click", () => {
    resetForm();
});

logoutButton.addEventListener("click", () => {
    localStorage.removeItem("token");
    window.location.href = "login.html";
});

seedButton.addEventListener("click", seedExercises);
exerciseForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    showMessage("");

    const name = exerciseNameInput.value.trim();
    if (!name) {
        showMessage("Exercise name is required", "error");
        return;
    }

    const category = exerciseCategorySelect.value;
    const isWeighted = exerciseWeightedSelect.value === "weighted";

    const payload = {
        name,
        category,
        is_weighted: isWeighted,
    };

    const exerciseId = exerciseIdInput.value;
    if (exerciseId) {
        await updateExercise(exerciseId, payload);
    } else {
        await createExercise(payload);
    }
});
exerciseCancelButton.addEventListener("click", () => {
    resetExerciseForm();
});
themeToggle.addEventListener("click", () => {
    const nextMode = document.body.classList.contains("theme-dark") ? "light" : "dark";
    saveTheme(nextMode);
});

async function init() {
    if (!requireAuth()) return;
    applyTheme(localStorage.getItem("theme") || "light");
    await loadMe();
    await loadExercises();
    await loadEntries();
    resetExerciseForm();
    resetForm();
}

init();
