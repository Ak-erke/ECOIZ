import Foundation

enum EcoLevel: String, CaseIterable, Codable {
    case level1 = "Эко-новичок"
    case level2 = "Эко-исследователь"
    case level3 = "Эко-помощник"
    case level4 = "Хранитель природы"
    case level5 = "Зеленый герой"
    case level6 = "Эко-наставник"
    case level7 = "Защитник планеты"
    case level8 = "Мастер устойчивости"
    case level9 = "Амбассадор Eco Iz"
    case level10 = "Хранитель Земли"

    static func from(points: Int) -> EcoLevel {
        switch points {
        case 0..<200:
            return .level1
        case 200..<400:
            return .level2
        case 400..<700:
            return .level3
        case 700..<1100:
            return .level4
        case 1100..<1600:
            return .level5
        case 1600..<2200:
            return .level6
        case 2200..<3000:
            return .level7
        case 3000..<4000:
            return .level8
        case 4000..<5500:
            return .level9
        default:
            return .level10
        }
    }

    var number: Int {
        switch self {
        case .level1: return 1
        case .level2: return 2
        case .level3: return 3
        case .level4: return 4
        case .level5: return 5
        case .level6: return 6
        case .level7: return 7
        case .level8: return 8
        case .level9: return 9
        case .level10: return 10
        }
    }

    var lowerBound: Int {
        switch self {
        case .level1: return 0
        case .level2: return 200
        case .level3: return 400
        case .level4: return 700
        case .level5: return 1100
        case .level6: return 1600
        case .level7: return 2200
        case .level8: return 3000
        case .level9: return 4000
        case .level10: return 5500
        }
    }

    var upperBoundExclusive: Int? {
        switch self {
        case .level1: return 200
        case .level2: return 400
        case .level3: return 700
        case .level4: return 1100
        case .level5: return 1600
        case .level6: return 2200
        case .level7: return 3000
        case .level8: return 4000
        case .level9: return 5500
        case .level10: return nil
        }
    }
}

enum ActivityCategory: String, CaseIterable, Identifiable, Codable {
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

struct EcoActivity: Identifiable, Codable {
    let id: String
    let category: ActivityCategory
    let title: String
    let co2Saved: Double
    let points: Int
    let createdAt: Date

    init(
        id: String = UUID().uuidString,
        category: ActivityCategory,
        title: String,
        co2Saved: Double,
        points: Int,
        createdAt: Date
    ) {
        self.id = id
        self.category = category
        self.title = title
        self.co2Saved = co2Saved
        self.points = points
        self.createdAt = createdAt
    }
}

struct UserProfile: Codable {
    let id: String
    var fullName: String
    var email: String
    var points: Int
    var streakDays: Int
    var co2SavedTotal: Double

    var level: EcoLevel {
        EcoLevel.from(points: points)
    }

    init(
        id: String = "local-user",
        fullName: String,
        email: String,
        points: Int,
        streakDays: Int,
        co2SavedTotal: Double
    ) {
        self.id = id
        self.fullName = fullName
        self.email = email
        self.points = points
        self.streakDays = streakDays
        self.co2SavedTotal = co2SavedTotal
    }
}

struct Challenge: Identifiable, Codable {
    let id: String
    let title: String
    let description: String
    let targetCount: Int
    var currentCount: Int
    let rewardPoints: Int
    let badgeSymbol: String
    let badgeTintHex: UInt32
    let badgeBackgroundHex: UInt32
    var isClaimed: Bool

    var isCompleted: Bool {
        currentCount >= targetCount
    }

    init(
        id: String = UUID().uuidString,
        title: String,
        description: String,
        targetCount: Int,
        currentCount: Int,
        rewardPoints: Int,
        badgeSymbol: String,
        badgeTintHex: UInt32,
        badgeBackgroundHex: UInt32,
        isClaimed: Bool = false
    ) {
        self.id = id
        self.title = title
        self.description = description
        self.targetCount = targetCount
        self.currentCount = currentCount
        self.rewardPoints = rewardPoints
        self.badgeSymbol = badgeSymbol
        self.badgeTintHex = badgeTintHex
        self.badgeBackgroundHex = badgeBackgroundHex
        self.isClaimed = isClaimed
    }
}

enum PostMediaKind: String, Codable {
    case photo
    case video
}

struct PostMediaAttachment: Identifiable, Codable {
    let id: String
    let kind: PostMediaKind
    let data: Data

    private enum CodingKeys: String, CodingKey {
        case id
        case kind
        case base64Data
    }

    init(id: String = UUID().uuidString, kind: PostMediaKind, data: Data) {
        self.id = id
        self.kind = kind
        self.data = data
    }

    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        id = try container.decodeIfPresent(String.self, forKey: .id) ?? UUID().uuidString
        kind = try container.decode(PostMediaKind.self, forKey: .kind)
        let base64 = try container.decode(String.self, forKey: .base64Data)
        guard let decoded = Data(base64Encoded: base64) else {
            throw DecodingError.dataCorruptedError(forKey: .base64Data, in: container, debugDescription: "Invalid base64 media data")
        }
        data = decoded
    }

    func encode(to encoder: Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(id, forKey: .id)
        try container.encode(kind, forKey: .kind)
        try container.encode(data.base64EncodedString(), forKey: .base64Data)
    }
}

struct EcoPost: Identifiable, Codable {
    let id: String
    let author: String
    let text: String
    let createdAt: Date
    let media: [PostMediaAttachment]

    init(
        id: String = UUID().uuidString,
        author: String,
        text: String,
        createdAt: Date,
        media: [PostMediaAttachment]
    ) {
        self.id = id
        self.author = author
        self.text = text
        self.createdAt = createdAt
        self.media = media
    }
}

struct ChatMessage: Identifiable, Codable {
    let id: String
    let isUser: Bool
    let text: String
    let createdAt: Date

    init(id: String = UUID().uuidString, isUser: Bool, text: String, createdAt: Date) {
        self.id = id
        self.isUser = isUser
        self.text = text
        self.createdAt = createdAt
    }
}
