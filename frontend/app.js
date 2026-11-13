const statusEl = document.getElementById("status");
const listEl = document.getElementById("students");
const makeGroupsButton = document.getElementById("make-groups");
const groupsStatusEl = document.getElementById("groups-status");
const groupsRoot = document.getElementById("groups-root");

// Display order matches the groups mockup. Cluster numbers come from the API:
// 0 is the data/stats center, 2 is the programming and frontend center,
// 1 is the pitch center.
const KINDS = [
  { key: "0", name: "Analyst", slug: "analyst" },
  { key: "2", name: "Builder", slug: "builder" },
  { key: "1", name: "Presenter", slug: "presenter" },
];

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

function setGroupsStatus(message, isError) {
  groupsStatusEl.hidden = false;
  groupsStatusEl.classList.toggle("error", isError);
  groupsStatusEl.textContent = message;
}

function clearGroupsStatus() {
  groupsStatusEl.hidden = true;
  groupsStatusEl.classList.remove("error");
  groupsStatusEl.textContent = "";
}

function memberNames(group) {
  if (!Array.isArray(group.members)) {
    return [];
  }
  return group.members.filter((name) => typeof name === "string");
}

function kindCount(counts, key) {
  const value = Number(counts?.[key]);
  return Number.isFinite(value) ? value : 0;
}

function kindsFor(counts) {
  const known = new Set(KINDS.map((kind) => kind.key));
  const extras = Object.keys(counts || {})
    .filter((key) => !known.has(String(key)))
    .sort()
    .map((key) => ({ key: String(key), name: `Cluster ${key}`, slug: "presenter" }));
  return KINDS.concat(extras);
}

function missingKinds(group) {
  const counts = group.cluster_counts || {};
  return kindsFor(counts).filter((kind) => kindCount(counts, kind.key) === 0);
}

function joinList(items) {
  if (items.length <= 1) {
    return items[0] || "";
  }
  if (items.length === 2) {
    return `${items[0]} and ${items[1]}`;
  }
  return `${items.slice(0, -1).join(", ")}, and ${items.at(-1)}`;
}

function sizeNote(groups) {
  const tally = new Map();
  for (const group of groups) {
    const size = memberNames(group).length;
    tally.set(size, (tally.get(size) || 0) + 1);
  }
  const parts = [...tally.entries()]
    .sort((left, right) => right[0] - left[0])
    .map(([size, count]) => {
      const groupVerb = count === 1 ? "group has" : "groups have";
      const studentNoun = size === 1 ? "student" : "students";
      return `${count} ${groupVerb} ${size} ${studentNoun}`;
    });
  const summary = parts.length > 1
    ? `${parts.slice(0, -1).join(", ")} and ${parts.at(-1)}`
    : parts[0];
  return `${summary}. Bar length is that kind’s share of the group.`;
}

function footnote(groups) {
  const totals = new Map(KINDS.map((kind) => [kind.key, 0]));
  for (const group of groups) {
    const counts = group.cluster_counts || {};
    for (const kind of kindsFor(counts)) {
      totals.set(kind.key, (totals.get(kind.key) || 0) + kindCount(counts, kind.key));
    }
  }
  const studentTotal = groups.reduce((sum, group) => sum + memberNames(group).length, 0);
  const kindSentence = KINDS.map((kind) => {
    const count = totals.get(kind.key) || 0;
    const noun = count === 1 ? kind.name : `${kind.name}s`;
    return `${count} ${noun}`;
  });
  const sentences = [
    `${joinList(kindSentence)} (${studentTotal} students).`,
  ];
  for (const kind of KINDS) {
    const groupNumbers = groups
      .filter((group) => kindCount(group.cluster_counts, kind.key) === 0)
      .map((group) => group.group);
    if (groupNumbers.length > 0) {
      const label = groupNumbers.length === 1 ? "Group" : "Groups";
      sentences.push(`${label} ${joinList(groupNumbers.map(String))} ${groupNumbers.length === 1 ? "is" : "are"} missing ${kind.name}.`);
    }
  }
  return sentences.join(" ");
}

function element(tag, className, text) {
  const node = document.createElement(tag);
  if (className) {
    node.className = className;
  }
  if (text != null) {
    node.textContent = text;
  }
  return node;
}

function renderGroups(data) {
  const groups = Array.isArray(data.groups) ? data.groups : [];
  if (groups.length === 0) {
    groupsRoot.replaceChildren();
    setGroupsStatus("No groups to show.", false);
    return;
  }

  clearGroupsStatus();
  const studentTotal = groups.reduce((sum, group) => sum + memberNames(group).length, 0);
  const groupTotal = Number.isFinite(Number(data.n_groups)) ? Number(data.n_groups) : groups.length;
  const missingTotal = Number.isFinite(Number(data.groups_missing_a_cluster))
    ? Number(data.groups_missing_a_cluster)
    : groups.filter((group) => missingKinds(group).length > 0).length;

  const wrap = element("div", "wrap");
  const header = element("header", "page");
  header.append(
    element("h1", null, "Class Project Groups"),
    element("p", "lede", "Group lists show member names only. The three student kinds — Analyst, Builder, and Presenter — are summarized for each group."),
  );

  const summary = element("section", "summary");
  summary.setAttribute("aria-label", "Class summary");
  summary.append(
    statCard(studentTotal, "Students", false),
    statCard(groupTotal, "Groups", false),
    statCard(missingTotal, "Groups missing a kind", missingTotal > 0),
  );

  const grid = element("div", "grid");
  for (const group of groups) {
    grid.append(groupCard(group));
  }

  const legend = element("p", "legend");
  for (const kind of KINDS) {
    const item = element("span");
    const swatch = element("i", `swatch ${kind.slug}`);
    swatch.setAttribute("aria-hidden", "true");
    item.append(swatch, document.createTextNode(kind.name));
    legend.append(item);
  }

  wrap.append(
    header,
    summary,
    element("p", "size-note", sizeNote(groups)),
    element("h2", "groups-heading", "Groups"),
    legend,
    grid,
    element("p", "footnote", footnote(groups)),
  );
  groupsRoot.replaceChildren(wrap);
  groupsRoot.scrollIntoView({ behavior: "smooth", block: "start" });
}

function statCard(value, label, warn) {
  const card = element("article", warn ? "stat stat-warn" : "stat");
  card.append(
    element("p", "stat-value", String(value)),
    element("p", "stat-label", label),
  );
  return card;
}

function groupCard(group) {
  const names = memberNames(group);
  const size = names.length;
  const counts = group.cluster_counts || {};
  const missing = missingKinds(group);
  const card = element("article", missing.length > 0 ? "group is-missing" : "group");
  const head = element("div", "group-head");
  const studentNoun = size === 1 ? "student" : "students";
  head.append(
    element("h3", null, `Group ${group.group}`),
    element("p", "count", `${size} ${studentNoun}`),
  );
  card.append(head);
  if (missing.length > 0) {
    card.append(element("p", "warning", `Warning: this group is missing ${joinList(missing.map((kind) => kind.name))}.`));
  }

  const members = element("ul", "members");
  for (const name of names) {
    members.append(element("li", null, name));
  }
  card.append(members);

  const kinds = element("div", "kinds");
  for (const kind of kindsFor(counts)) {
    const count = kindCount(counts, kind.key);
    const row = element("div", "kind");
    const track = element("div", "track");
    const fill = element("span", `fill ${kind.slug}`);
    track.setAttribute("role", "img");
    track.setAttribute("aria-label", `${kind.name}: ${count} of ${size}`);
    fill.style.width = size === 0 ? "0%" : `${(count / size) * 100}%`;
    track.append(fill);
    row.append(
      element("span", "kind-name", kind.name),
      element("span", "kind-count", String(count)),
      track,
    );
    kinds.append(row);
  }
  card.append(element("p", "kinds-label", "Student kinds"), kinds);
  return card;
}

async function loadGroups() {
  makeGroupsButton.disabled = true;
  groupsRoot.replaceChildren();
  setGroupsStatus("Loading groups…", false);
  try {
    const response = await fetch("/api/groups");
    if (!response.ok) {
      throw new Error(`Request failed (${response.status})`);
    }
    renderGroups(await response.json());
  } catch (error) {
    groupsRoot.replaceChildren();
    setGroupsStatus("Could not load groups.", true);
    console.error(error);
  } finally {
    makeGroupsButton.disabled = false;
  }
}

makeGroupsButton.addEventListener("click", loadGroups);
loadStudents();
