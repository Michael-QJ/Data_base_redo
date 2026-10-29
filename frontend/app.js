const statusEl = document.getElementById("status");
const listEl = document.getElementById("students");

async function loadStudents() {
  try {
    const response = await fetch("/api/students");
    if (!response.ok) {
      throw new Error(`Request failed (${response.status})`);
    }

    const data = await response.json();
    const students = data.students ?? [];

    listEl.replaceChildren();
    for (const student of students) {
      const item = document.createElement("li");
      item.textContent = student.name;
      listEl.appendChild(item);
    }

    statusEl.textContent =
      students.length === 1
        ? "1 student"
        : `${students.length} students`;
  } catch (error) {
    statusEl.classList.add("error");
    statusEl.textContent = "Could not load student names.";
    console.error(error);
  }
}

loadStudents();
