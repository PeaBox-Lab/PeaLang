# Projects and Modules

A project uses `pea.json` with `manifest_version`, `project.name`, `project.version`, `project.entry`, and a `dependencies` dictionary. Module resolution checks explicit relative paths, the project `modules/` folder, declared local dependencies, then the current directory.
