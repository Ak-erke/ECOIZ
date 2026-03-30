import Foundation
import Combine

@MainActor
final class AppState: ObservableObject {
    @Published var isAuthenticated = false
    @Published var isRestoringSession = false
    @Published var isAuthenticating = false
    @Published var isSubmittingActivity = false
    @Published var isPosting = false
    @Published var isSendingMessage = false
    @Published var isClaimingChallenge = false
    @Published var alertMessage: String?
    @Published var levelUpLevel: EcoLevel?

    @Published var user = UserProfile(
        fullName: "Пользователь",
        email: "user@ecoiz.app",
        points: 0,
        streakDays: 0,
        co2SavedTotal: 0
    )
    @Published var activities: [EcoActivity] = []
    @Published var challenges: [Challenge] = []
    @Published var posts: [EcoPost] = []
    @Published var chatMessages: [ChatMessage] = []
    @Published var communityImpact = CommunityImpact(
        totalUsers: 0,
        activeUsers: 0,
        totalActivities: 0,
        totalPosts: 0,
        totalChallengesCompleted: 0,
        totalCo2Saved: 0,
        totalPoints: 0
    )

    private let apiClient: APIClient
    private var didAttemptSessionRestore = false

    let templatesByCategory: [ActivityCategory: [ActivityTemplate]] = [
        .transport: [
            ActivityTemplate(title: "Пешая прогулка", estimatedCO2: 1.5, points: 20),
            ActivityTemplate(title: "Мотоцикл", estimatedCO2: 0.3, points: 5),
            ActivityTemplate(title: "Велосипед", estimatedCO2: 2.0, points: 25),
            ActivityTemplate(title: "Самокат", estimatedCO2: 0.8, points: 15),
            ActivityTemplate(title: "Машина", estimatedCO2: 0.0, points: 0),
            ActivityTemplate(title: "Общ. транспорт", estimatedCO2: 1.0, points: 15),
            ActivityTemplate(title: "Поезд", estimatedCO2: 1.2, points: 15),
            ActivityTemplate(title: "Совместная поездка", estimatedCO2: 1.3, points: 18)
        ],
        .plastic: [
            ActivityTemplate(title: "Без пакета", estimatedCO2: 0.05, points: 10),
            ActivityTemplate(title: "Многоразовая сумка", estimatedCO2: 0.08, points: 15),
            ActivityTemplate(title: "Многоразовая бутылка", estimatedCO2: 0.12, points: 20),
            ActivityTemplate(title: "Сдал пластик", estimatedCO2: 0.18, points: 25)
        ],
        .water: [
            ActivityTemplate(title: "Короткий душ", estimatedCO2: 0.35, points: 15),
            ActivityTemplate(title: "Закрыл кран вовремя", estimatedCO2: 0.08, points: 10),
            ActivityTemplate(title: "Полная загрузка стирки", estimatedCO2: 0.25, points: 20),
            ActivityTemplate(title: "Устранил утечку", estimatedCO2: 0.6, points: 30),
            ActivityTemplate(title: "Установил аэратор", estimatedCO2: 0.45, points: 25)
        ],
        .waste: [
            ActivityTemplate(title: "Сортировка", estimatedCO2: 0.2, points: 15),
            ActivityTemplate(title: "Сдал вторсырье", estimatedCO2: 0.3, points: 20),
            ActivityTemplate(title: "Компост", estimatedCO2: 0.25, points: 20)
        ],
        .energy: [
            ActivityTemplate(title: "Выключил свет", estimatedCO2: 0.18, points: 10),
            ActivityTemplate(title: "Отключил приборы из сети", estimatedCO2: 0.12, points: 15),
            ActivityTemplate(title: "Использую LED-лампы", estimatedCO2: 0.4, points: 20),
            ActivityTemplate(title: "Использую дневной свет", estimatedCO2: 0.15, points: 15)
        ]
    ]

    init(apiClient: APIClient? = nil) {
        self.apiClient = apiClient ?? APIClient()
    }

    func restoreSessionIfNeeded() async {
        guard !didAttemptSessionRestore else { return }
        didAttemptSessionRestore = true
        await restoreSession()
    }

    func restoreSession() async {
        guard apiClient.hasStoredToken else { return }
        alertMessage = nil
        isRestoringSession = true
        defer { isRestoringSession = false }

        do {
            try await loadBootstrap()
            isAuthenticated = true
        } catch {
            apiClient.clearToken()
            clearSession()
            present(error)
        }
    }

    @discardableResult
    func signIn(email: String, password: String) async -> Bool {
        guard !email.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty, !password.isEmpty else {
            return false
        }

        alertMessage = nil
        isAuthenticating = true
        defer { isAuthenticating = false }

        do {
            _ = try await apiClient.login(email: email, password: password)
            try await loadBootstrap()
            isAuthenticated = true
            return true
        } catch {
            present(error)
            return false
        }
    }

    @discardableResult
    func register(name: String, email: String, password: String) async -> Bool {
        guard !name.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty,
              !email.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty,
              !password.isEmpty else {
            return false
        }

        alertMessage = nil
        isAuthenticating = true
        defer { isAuthenticating = false }

        do {
            _ = try await apiClient.register(name: name, email: email, password: password)
            try await loadBootstrap()
            isAuthenticated = true
            return true
        } catch {
            present(error)
            return false
        }
    }

    func signOut() {
        apiClient.clearToken()
        clearSession()
    }

    @discardableResult
    func addActivity(
        category: ActivityCategory,
        title: String,
        co2: Double,
        points: Int,
        note: String? = nil,
        media: [PostMediaAttachment] = [],
        shareToNews: Bool = true
    ) async -> Bool {
        alertMessage = nil
        isSubmittingActivity = true
        defer { isSubmittingActivity = false }

        do {
            let response = try await apiClient.addActivity(
                category: category,
                title: title,
                co2: co2,
                points: points,
                note: note,
                media: media,
                shareToNews: shareToNews
            )
            updateUser(response.user, animateLevelUp: true)
            challenges = response.challenges
            activities.insert(response.activity, at: 0)
            if shareToNews {
                do {
                    posts = try await apiClient.fetchPosts()
                } catch {
                    present(error)
                }
            }
            return true
        } catch {
            present(error)
            return false
        }
    }

    @discardableResult
    func addPost(text: String, media: [PostMediaAttachment] = []) async -> Bool {
        let trimmed = text.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmed.isEmpty || !media.isEmpty else { return false }

        alertMessage = nil
        isPosting = true
        defer { isPosting = false }

        do {
            let post = try await apiClient.addPost(text: trimmed, media: media)
            posts.insert(post, at: 0)
            return true
        } catch {
            present(error)
            return false
        }
    }

    @discardableResult
    func sendMessageToAI(_ text: String) async -> Bool {
        let trimmed = text.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmed.isEmpty else { return false }

        alertMessage = nil
        isSendingMessage = true
        defer { isSendingMessage = false }

        do {
            let newMessages = try await apiClient.sendMessage(trimmed)
            chatMessages.append(contentsOf: newMessages)
            return true
        } catch {
            present(error)
            return false
        }
    }

    @discardableResult
    func claimChallenge(_ challengeID: String) async -> Challenge? {
        alertMessage = nil
        isClaimingChallenge = true
        defer { isClaimingChallenge = false }

        do {
            let response = try await apiClient.claimChallenge(id: challengeID)
            updateUser(response.user, animateLevelUp: true)
            challenges = response.challenges
            return response.challenge
        } catch {
            present(error)
            return nil
        }
    }

    private func loadBootstrap() async throws {
        let bootstrap = try await apiClient.bootstrap()
        updateUser(bootstrap.user, animateLevelUp: false)
        activities = bootstrap.activities
        challenges = bootstrap.challenges
        posts = bootstrap.posts
        chatMessages = bootstrap.chatMessages
        communityImpact = bootstrap.communityImpact
        if chatMessages.isEmpty {
            chatMessages = [
                ChatMessage(isUser: false, text: "Привет! Я эко-ИИ. Помогу улучшить твои экопривычки и мотивацию.", createdAt: Date())
            ]
        }
    }

    private func clearSession() {
        isAuthenticated = false
        levelUpLevel = nil
        user = UserProfile(
            fullName: "Пользователь",
            email: "user@ecoiz.app",
            points: 0,
            streakDays: 0,
            co2SavedTotal: 0
        )
        activities = []
        challenges = []
        posts = []
        communityImpact = CommunityImpact(
            totalUsers: 0,
            activeUsers: 0,
            totalActivities: 0,
            totalPosts: 0,
            totalChallengesCompleted: 0,
            totalCo2Saved: 0,
            totalPoints: 0
        )
        chatMessages = [
            ChatMessage(isUser: false, text: "Привет! Я эко-ИИ. Помогу улучшить твои экопривычки и мотивацию.", createdAt: Date())
        ]
    }

    private func present(_ error: Error) {
        alertMessage = (error as? LocalizedError)?.errorDescription ?? error.localizedDescription
    }

    private func updateUser(_ newUser: UserProfile, animateLevelUp: Bool) {
        let previousLevel = user.level
        user = newUser
        guard animateLevelUp, newUser.level.number > previousLevel.number else { return }
        levelUpLevel = newUser.level
    }
}
