import AVFoundation
import SwiftUI
import UIKit

enum EcoFeedback {
    private static let sampleRate = 44_100
    private static var cachedPlayers: [String: AVAudioPlayer] = [:]

    static func playActivitySaved() {
        UINotificationFeedbackGenerator().notificationOccurred(.success)
        playChime(
            key: "activitySaved",
            notes: [
                (659.25, 0.12),
                (783.99, 0.14),
            ]
        )
    }

    static func playLevelUp() {
        let generator = UINotificationFeedbackGenerator()
        generator.prepare()
        generator.notificationOccurred(.success)
        UIImpactFeedbackGenerator(style: .rigid).impactOccurred(intensity: 0.9)
        playChime(
            key: "levelUp",
            notes: [
                (523.25, 0.10),
                (659.25, 0.12),
                (783.99, 0.14),
                (1046.50, 0.24),
            ]
        )
    }

    private static func playChime(key: String, notes: [(Double, Double)]) {
        configureSessionIfNeeded()
        if let player = cachedPlayers[key] {
            player.currentTime = 0
            player.play()
            return
        }

        guard let data = makeWaveData(notes: notes),
              let player = try? AVAudioPlayer(data: data) else {
            return
        }
        player.prepareToPlay()
        cachedPlayers[key] = player
        player.play()
    }

    private static func configureSessionIfNeeded() {
        let session = AVAudioSession.sharedInstance()
        try? session.setCategory(.ambient, options: [.mixWithOthers])
        try? session.setActive(true)
    }

    private static func makeWaveData(notes: [(Double, Double)]) -> Data? {
        var pcm = Data()
        let amplitude = 0.28
        let pauseSamples = Int(Double(sampleRate) * 0.018)

        for (frequency, duration) in notes {
            let samples = Int(Double(sampleRate) * duration)
            for index in 0..<samples {
                let t = Double(index) / Double(sampleRate)
                let envelope = ADSREnvelope.value(
                    progress: Double(index) / Double(max(samples - 1, 1)),
                    attack: 0.12,
                    decay: 0.18,
                    sustain: 0.72,
                    release: 0.20
                )
                let wave =
                    sin(2 * .pi * frequency * t)
                    + 0.45 * sin(2 * .pi * frequency * 2 * t)
                    + 0.18 * sin(2 * .pi * frequency * 3 * t)
                let sample = max(-1.0, min(1.0, wave * amplitude * envelope))
                let value = Int16(sample * Double(Int16.max))
                var littleEndian = value.littleEndian
                pcm.append(Data(bytes: &littleEndian, count: MemoryLayout<Int16>.size))
            }

            if pauseSamples > 0 {
                let silence = Data(repeating: 0, count: pauseSamples * MemoryLayout<Int16>.size)
                pcm.append(silence)
            }
        }

        let byteRate = sampleRate * MemoryLayout<Int16>.size
        let blockAlign = UInt16(MemoryLayout<Int16>.size)
        let subchunk2Size = UInt32(pcm.count)
        let chunkSize = 36 + subchunk2Size

        var data = Data()
        data.append("RIFF".data(using: .ascii)!)
        data.append(contentsOf: chunkSize.littleEndianBytes)
        data.append("WAVE".data(using: .ascii)!)
        data.append("fmt ".data(using: .ascii)!)
        data.append(contentsOf: UInt32(16).littleEndianBytes)
        data.append(contentsOf: UInt16(1).littleEndianBytes)
        data.append(contentsOf: UInt16(1).littleEndianBytes)
        data.append(contentsOf: UInt32(sampleRate).littleEndianBytes)
        data.append(contentsOf: UInt32(byteRate).littleEndianBytes)
        data.append(contentsOf: blockAlign.littleEndianBytes)
        data.append(contentsOf: UInt16(16).littleEndianBytes)
        data.append("data".data(using: .ascii)!)
        data.append(contentsOf: subchunk2Size.littleEndianBytes)
        data.append(pcm)
        return data
    }
}

private enum ADSREnvelope {
    static func value(progress: Double, attack: Double, decay: Double, sustain: Double, release: Double) -> Double {
        switch progress {
        case ..<attack:
            return progress / max(attack, 0.0001)
        case ..<(attack + decay):
            let normalized = (progress - attack) / max(decay, 0.0001)
            return 1.0 - normalized * (1.0 - sustain)
        case ..<(1.0 - release):
            return sustain
        default:
            let normalized = (progress - (1.0 - release)) / max(release, 0.0001)
            return sustain * max(0.0, 1.0 - normalized)
        }
    }
}

private extension FixedWidthInteger {
    var littleEndianBytes: [UInt8] {
        withUnsafeBytes(of: self.littleEndian) { Array($0) }
    }
}
