import Foundation

enum APIError: LocalizedError {
    case invalidURL
    case invalidResponse
    case server(String)
    case unauthorized

    var errorDescription: String? {
        switch self {
        case .invalidURL:
            return "Некорректный адрес backend."
        case .invalidResponse:
            return "Backend вернул некорректный ответ."
        case .server(let message):
            return message
        case .unauthorized:
            return "Сессия истекла. Войди снова."
        }
    }
}

private struct APIErrorResponse: Decodable {
    let error: String
}

struct AuthSessionResponse: Decodable {
    let token: String
    let user: UserProfile
}

struct BootstrapResponse: Decodable {
    let user: UserProfile
    let activities: [EcoActivity]
    let challenges: [Challenge]
    let posts: [EcoPost]
    let chatMessages: [ChatMessage]
}

struct ActivityMutationResponse: Decodable {
    let activity: EcoActivity
    let user: UserProfile
    let challenges: [Challenge]
}

struct ChallengeClaimResponse: Decodable {
    let user: UserProfile
    let challenge: Challenge
    let challenges: [Challenge]
}

private struct PostEnvelope: Decodable {
    let post: EcoPost
}

private struct PostsEnvelope: Decodable {
    let posts: [EcoPost]
}

private struct ChatEnvelope: Decodable {
    let messages: [ChatMessage]
}

private struct LoginRequest: Encodable {
    let email: String
    let password: String
}

private struct RegisterRequest: Encodable {
    let fullName: String
    let email: String
    let password: String
}

private struct ActivityRequest: Encodable {
    let category: String
    let title: String
    let co2Saved: Double
    let points: Int
    let note: String
    let media: [PostMediaAttachment]
    let shareToNews: Bool
}

private struct PostRequest: Encodable {
    let text: String
    let media: [PostMediaAttachment]
}

private struct ChatRequest: Encodable {
    let text: String
}

final class APIClient {
    private let session: URLSession
    private let encoder: JSONEncoder
    private let decoder: JSONDecoder
    private let tokenKey = "ecoiz.backend.token"
    private let baseURL: URL

    init(session: URLSession = .shared) {
        self.session = session
        self.encoder = APIClient.makeEncoder()
        self.decoder = APIClient.makeDecoder()
        guard let url = URL(string: Self.resolveBaseURL()) else {
            fatalError("Invalid EcoIZ backend URL")
        }
        self.baseURL = url
    }

    var hasStoredToken: Bool {
        storedToken != nil
    }

    func clearToken() {
        UserDefaults.standard.removeObject(forKey: tokenKey)
    }

    func login(email: String, password: String) async throws -> AuthSessionResponse {
        let response: AuthSessionResponse = try await request(
            path: "/auth/login",
            method: "POST",
            body: LoginRequest(email: email, password: password),
            requiresAuth: false
        )
        storedToken = response.token
        return response
    }

    func register(name: String, email: String, password: String) async throws -> AuthSessionResponse {
        let response: AuthSessionResponse = try await request(
            path: "/auth/register",
            method: "POST",
            body: RegisterRequest(fullName: name, email: email, password: password),
            requiresAuth: false
        )
        storedToken = response.token
        return response
    }

    func bootstrap() async throws -> BootstrapResponse {
        try await request(path: "/bootstrap", method: "GET", requiresAuth: true)
    }

    func fetchPosts() async throws -> [EcoPost] {
        let response: PostsEnvelope = try await request(path: "/posts", method: "GET", requiresAuth: true)
        return response.posts
    }

    func addActivity(
        category: ActivityCategory,
        title: String,
        co2: Double,
        points: Int,
        note: String?,
        media: [PostMediaAttachment],
        shareToNews: Bool
    ) async throws -> ActivityMutationResponse {
        try await request(
            path: "/activities",
            method: "POST",
            body: ActivityRequest(
                category: category.rawValue,
                title: title,
                co2Saved: co2,
                points: points,
                note: note ?? "",
                media: media,
                shareToNews: shareToNews
            ),
            requiresAuth: true
        )
    }

    func addPost(text: String, media: [PostMediaAttachment]) async throws -> EcoPost {
        let response: PostEnvelope = try await request(
            path: "/posts",
            method: "POST",
            body: PostRequest(text: text, media: media),
            requiresAuth: true
        )
        return response.post
    }

    func sendMessage(_ text: String) async throws -> [ChatMessage] {
        let response: ChatEnvelope = try await request(
            path: "/chat/messages",
            method: "POST",
            body: ChatRequest(text: text),
            requiresAuth: true
        )
        return response.messages
    }

    func claimChallenge(id: String) async throws -> ChallengeClaimResponse {
        try await request(
            path: "/challenges/\(id)/claim",
            method: "POST",
            requiresAuth: true
        )
    }

    private func request<Response: Decodable>(
        path: String,
        method: String,
        requiresAuth: Bool
    ) async throws -> Response {
        try await request(path: path, method: method, body: Optional<String>.none, requiresAuth: requiresAuth)
    }

    private func request<Response: Decodable, Body: Encodable>(
        path: String,
        method: String,
        body: Body?,
        requiresAuth: Bool
    ) async throws -> Response {
        let endpoint = baseURL.appendingPathComponent(path.trimmingCharacters(in: CharacterSet(charactersIn: "/")))
        var request = URLRequest(url: endpoint)
        request.httpMethod = method
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        if requiresAuth {
            guard let storedToken else {
                throw APIError.unauthorized
            }
            request.setValue("Bearer \(storedToken)", forHTTPHeaderField: "Authorization")
        }

        if let body {
            request.httpBody = try encoder.encode(body)
        }

        let (data, response) = try await session.data(for: request)
        guard let httpResponse = response as? HTTPURLResponse else {
            throw APIError.invalidResponse
        }

        if httpResponse.statusCode == 401 {
            clearToken()
            throw APIError.unauthorized
        }

        guard (200...299).contains(httpResponse.statusCode) else {
            if let errorResponse = try? decoder.decode(APIErrorResponse.self, from: data) {
                throw APIError.server(errorResponse.error)
            }
            throw APIError.invalidResponse
        }

        do {
            return try decoder.decode(Response.self, from: data)
        } catch {
            #if DEBUG
            let rawBody = String(data: data, encoding: .utf8) ?? "<non-utf8>"
            print("EcoIZ decode error for \(path): \(error)")
            print("EcoIZ raw response: \(rawBody)")
            #endif
            throw APIError.invalidResponse
        }
    }

    private var storedToken: String? {
        get { UserDefaults.standard.string(forKey: tokenKey) }
        set {
            if let newValue {
                UserDefaults.standard.set(newValue, forKey: tokenKey)
            } else {
                UserDefaults.standard.removeObject(forKey: tokenKey)
            }
        }
    }

    private static func resolveBaseURL() -> String {
        return "http://127.0.0.1:8000"
    }

    private static func makeDecoder() -> JSONDecoder {
        let decoder = JSONDecoder()
        decoder.dateDecodingStrategy = .custom { value in
            let container = try value.singleValueContainer()
            let raw = try container.decode(String.self)
            if let date = DateParsing.iso8601WithFractional.date(from: raw)
                ?? DateParsing.iso8601.date(from: raw)
                ?? DateParsing.postgresFractional.date(from: raw)
                ?? DateParsing.postgres.date(from: raw) {
                return date
            }
            throw DecodingError.dataCorruptedError(in: container, debugDescription: "Unsupported date: \(raw)")
        }
        return decoder
    }

    private static func makeEncoder() -> JSONEncoder {
        let encoder = JSONEncoder()
        encoder.dateEncodingStrategy = .custom { date, encoder in
            var container = encoder.singleValueContainer()
            try container.encode(DateParsing.iso8601WithFractional.string(from: date))
        }
        return encoder
    }
}

enum DateParsing {
    static let iso8601WithFractional: ISO8601DateFormatter = {
        let formatter = ISO8601DateFormatter()
        formatter.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
        return formatter
    }()

    static let iso8601: ISO8601DateFormatter = {
        let formatter = ISO8601DateFormatter()
        formatter.formatOptions = [.withInternetDateTime]
        return formatter
    }()

    static let postgresFractional: DateFormatter = {
        let formatter = DateFormatter()
        formatter.locale = Locale(identifier: "en_US_POSIX")
        formatter.timeZone = TimeZone(secondsFromGMT: 0)
        formatter.dateFormat = "yyyy-MM-dd'T'HH:mm:ss.SSSSSS"
        return formatter
    }()

    static let postgres: DateFormatter = {
        let formatter = DateFormatter()
        formatter.locale = Locale(identifier: "en_US_POSIX")
        formatter.timeZone = TimeZone(secondsFromGMT: 0)
        formatter.dateFormat = "yyyy-MM-dd'T'HH:mm:ss"
        return formatter
    }()
}
