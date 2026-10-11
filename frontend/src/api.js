const API_BASE_URL = "http://127.0.0.1:8000";

export async function getRepositoryGraph(repositoryName) {
    const response = await fetch(
        `${API_BASE_URL}/repositories/${repositoryName}/graph`
    );

    if (!response.ok) {
        throw new Error(
            `Failed to fetch repository graph: ${response.status}`
        );
    }

    return await response.json();
}


export async function getRepositoryFile(repositoryName, filePath) {
    const response = await fetch(
        `${API_BASE_URL}/repositories/${repositoryName}/files/${filePath}`
    );

    if (!response.ok) {
        throw new Error(
            `Failed to fetch repository file: ${response.status}`
        );
    }

    return await response.json();
}

export async function analyzeRepository(githubUrl) {

    const response = await fetch(
        `${API_BASE_URL}/repositories/analyze`,
        {
            method: "POST",

            headers: {
                "Content-Type": "application/json",
            },

            body: JSON.stringify({
                github_url: githubUrl,
            }),
        }
    );


    if (!response.ok) {

        let message =
            `Failed to analyze repository: ${response.status}`;

        try {

            const errorData =
                await response.json();

            if (errorData.detail) {
                message = errorData.detail;
            }

        } catch {
            // Keep default error message
        }

        throw new Error(message);
    }


    return await response.json();
}


export async function askRepositoryQuestion(
    repositoryName,
    question,
    topK = 5
) {
    const response = await fetch(
        `${API_BASE_URL}/repositories/${encodeURIComponent(repositoryName)}/ask`,
        {
            method: "POST",

            headers: {
                "Content-Type": "application/json",
            },

            body: JSON.stringify({
                question,
                top_k: topK,
            }),
        }
    );

    if (!response.ok) {
        let message = `Failed to ask repository question: ${response.status}`;

        try {
            const errorData = await response.json();

            if (errorData.detail) {
                message = errorData.detail;
            }
        } catch {
            // Keep the default error message.
        }

        throw new Error(message);
    }

    return await response.json();
}