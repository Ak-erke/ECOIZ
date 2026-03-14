import Foundation

enum EcoLevel: String, CaseIterable {
    case newHero = "Эко-новичок"
    case ecoWarrior = "Эко-воин"
    case planetGuardian = "Хранитель Земли"

    static func from(points: Int) -> EcoLevel {
        switch points {
        case 0..<120:
            return .newHero
        case 120..<320:
            return .ecoWarrior
        default:
            return .planetGuardian
        }
    }
}

enum ActivityCategory: String, CaseIterable, Identifiable {
    case transport = "Транспорт"
    case plastic = "Пластик"
    case water = "Вода"
    case waste = "Отходы"
    case energy = "Энергия"
    case custom = "Своя активность"

    var id: String { rawValue }
}

struct ActivityTemplate: Identifiable {
    let id = UUID()
    let title: String
    let estimatedCO2: Double
    let points: Int
}

struct EcoActivity: Identifiable {
    let id = UUID()
    let category: ActivityCategory
    let title: String
    let co2Saved: Double
    let points: Int
    let createdAt: Date
}

struct UserProfile {
    var fullName: String
    var email: String
    var points: Int
    var streakDays: Int
    var co2SavedTotal: Double
    var level: EcoLevel {
        EcoLevel.from(points: points)
    }
}

struct Challenge: Identifiable {
    let id = UUID()
    let title: String
    let description: String
    let targetCount: Int
    var currentCount: Int
    let rewardPoints: Int
    let badgeSymbol: String
    let badgeTintHex: UInt32
    let badgeBackgroundHex: UInt32

    var isCompleted: Bool {
        currentCount >= targetCount
    }
}

enum PostMediaKind {
    case photo
    case video
}

struct PostMediaAttachment: Identifiable {
    let id = UUID()
    let kind: PostMediaKind
    let data: Data
}

struct EcoPost: Identifiable {
    let id = UUID()
    let author: String
    let text: String
    let createdAt: Date
    let media: [PostMediaAttachment]
}

struct ChatMessage: Identifiable {
    let id = UUID()
    let isUser: Bool
    let text: String
    let createdAt: Date
}
