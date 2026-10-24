



from pathlib import Path
import networkx as nx


def normalize_path(path: str) -> str:
    """
    Convert Windows-style paths to POSIX-style paths.

    Example:
        core\\extractor.py
        ->
        core/extractor.py
    """
    return Path(path).as_posix()


def build_repository_graph(repository_analysis, dependency_data):

    graph = nx.DiGraph()

    repository_name = repository_analysis["repository"]

    # --------------------------------------------------
    # Repository Node
    # --------------------------------------------------

    repo_id = f"repo:{repository_name}"

    graph.add_node(
        repo_id,
        type="repository",
        name=repository_name,
    )

    # --------------------------------------------------
    # Process Files
    # --------------------------------------------------

    for file_info in repository_analysis["files"]:

        file_path = normalize_path(file_info["path"])

        file_id = f"file:{file_path}"

        # ----------------------------------------------
        # Create folder hierarchy
        # ----------------------------------------------

        path_parts = file_path.split("/")

        current_parent = repo_id
        current_path = ""

        for folder in path_parts[:-1]:

            if current_path:
                current_path += f"/{folder}"
            else:
                current_path = folder

            folder_id = f"folder:{current_path}"

            if not graph.has_node(folder_id):

                graph.add_node(
                    folder_id,
                    type="folder",
                    name=folder,
                    path=current_path,
                )

                graph.add_edge(
                    current_parent,
                    folder_id,
                    type="CONTAINS",
                )

            current_parent = folder_id

        # ----------------------------------------------
        # File node
        # ----------------------------------------------

        graph.add_node(
            file_id,
            type="file",
            name=file_info["name"],
            path=file_path,
            language=file_info["language"],
            size=file_info["size"],
            analysis=file_info.get("analysis", {}),
        )

        graph.add_edge(
            current_parent,
            file_id,
            type="CONTAINS",
        )

        # ----------------------------------------------
        # Analysis information
        # ----------------------------------------------

        analysis = file_info.get("analysis", {})

        # ----------------------------------------------
        # Classes
        # ----------------------------------------------

        for cls in analysis.get("classes", []):

            class_name = cls["name"]

            class_id = f"class:{file_path}:{class_name}"

            graph.add_node(
                class_id,
                type="class",
                name=class_name,
                file=file_path,
                line_start=cls.get("line_start"),
                line_end=cls.get("line_end"),
            )

            graph.add_edge(
                file_id,
                class_id,
                type="CONTAINS",
            )

            # ------------------------------------------
            # Methods
            # ------------------------------------------

            for method in cls.get("methods", []):

                method_name = method["name"]

                method_id = (
                    f"method:{file_path}:{class_name}:{method_name}"
                )

                graph.add_node(
                    method_id,
                    type="method",
                    name=method_name,
                    file=file_path,
                    class_name=class_name,
                    line_start=method.get("line_start"),
                    line_end=method.get("line_end"),
                )

                graph.add_edge(
                    class_id,
                    method_id,
                    type="CONTAINS",
                )

        # ----------------------------------------------
        # Top-level Functions
        # ----------------------------------------------

        for function in analysis.get("functions", []):

            function_name = function["name"]

            function_id = f"function:{file_path}:{function_name}"

            graph.add_node(
                function_id,
                type="function",
                name=function_name,
                file=file_path,
                line_start=function.get("line_start"),
                line_end=function.get("line_end"),
            )

            graph.add_edge(
                file_id,
                function_id,
                type="CONTAINS",
            )

    # --------------------------------------------------
    # Repository Statistics
    # --------------------------------------------------

    repository_node = graph.nodes[repo_id]

    repository_node["files"] = sum(
        1
        for _, data in graph.nodes(data=True)
        if data.get("type") == "file"
    )

    repository_node["folders"] = sum(
        1
        for _, data in graph.nodes(data=True)
        if data.get("type") == "folder"
    )

    repository_node["classes"] = sum(
        1
        for _, data in graph.nodes(data=True)
        if data.get("type") == "class"
    )

    repository_node["methods"] = sum(
        1
        for _, data in graph.nodes(data=True)
        if data.get("type") == "method"
    )

    repository_node["functions"] = sum(
        1
        for _, data in graph.nodes(data=True)
        if data.get("type") == "function"
    )

    # --------------------------------------------------
    # Folder Statistics
    # --------------------------------------------------

    for node_id, data in graph.nodes(data=True):

        if data.get("type") != "folder":
            continue

        folder_path = data["path"]
        folder_prefix = folder_path + "/"

        folder_files = 0
        folder_subfolders = 0
        folder_classes = 0
        folder_methods = 0
        folder_functions = 0

        # ----------------------------------------------
        # Count direct files and direct subfolders
        # ----------------------------------------------

        for _, child_data in graph.nodes(data=True):

            child_type = child_data.get("type")

            if child_type == "file":

                file_path = child_data.get("path", "")

                if file_path.startswith(folder_prefix):
                    remaining_path = file_path[len(folder_prefix):]

                    if "/" not in remaining_path:
                        folder_files += 1

            elif child_type == "folder":

                child_path = child_data.get("path", "")

                if child_path.startswith(folder_prefix):
                    remaining_path = child_path[len(folder_prefix):]

                    if "/" not in remaining_path:
                        folder_subfolders += 1

        # ----------------------------------------------
        # Count classes, methods, and functions
        # in this folder and its nested folders
        # ----------------------------------------------

        for _, child_data in graph.nodes(data=True):

            child_type = child_data.get("type")

            if child_type not in {
                "class",
                "method",
                "function",
            }:
                continue

            file_path = child_data.get("file", "")

            if file_path.startswith(folder_prefix):
                if child_type == "class":
                    folder_classes += 1

                elif child_type == "method":
                    folder_methods += 1

                elif child_type == "function":
                    folder_functions += 1

        data["files"] = folder_files
        data["subfolders"] = folder_subfolders
        data["classes"] = folder_classes
        data["methods"] = folder_methods
        data["functions"] = folder_functions

    # --------------------------------------------------
    # Dependency Edges
    # --------------------------------------------------

    for dependency in dependency_data["dependencies"]:

        source_path = normalize_path(dependency["source"])

        target_path = normalize_path(dependency["target"])

        source_id = f"file:{source_path}"
        target_id = f"file:{target_path}"

        if graph.has_node(source_id) and graph.has_node(target_id):

            graph.add_edge(
                source_id,
                target_id,
                type=dependency["type"],
            )

    return graph


def graph_to_json(graph):

    nodes = []

    for node_id, data in graph.nodes(data=True):

        nodes.append(
            {
                "id": node_id,
                **data,
            }
        )

    edges = []

    for source, target, data in graph.edges(data=True):

        edges.append(
            {
                "source": source,
                "target": target,
                **data,
            }
        )

    return {
        "nodes": nodes,
        "edges": edges,
    }