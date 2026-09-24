import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;

void main() {
  runApp(const PhishDetectorApp());
}

class PhishDetectorApp extends StatelessWidget {
  const PhishDetectorApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Phishing Detector',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        brightness: Brightness.dark,
        scaffoldBackgroundColor: const Color(0xFF0F1115),
        primarySwatch: Colors.blue,
        useMaterial3: true,
      ),
      home: const HomeScreen(),
    );
  }
}

// IMPORTANT: change this to your deployed API URL once you host it
// (e.g. on Render/Railway). For local testing on an Android emulator,
// use 10.0.2.2 instead of 127.0.0.1 to reach your computer's localhost.
const String apiBaseUrl = "http://10.0.2.2:5000";

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  final TextEditingController _controller = TextEditingController();
  Map<String, dynamic>? _result;
  bool _loading = false;
  String? _error;

  Future<void> _analyzeMessage() async {
    final message = _controller.text.trim();
    if (message.isEmpty) return;

    setState(() {
      _loading = true;
      _error = null;
      _result = null;
    });

    try {
      final response = await http.post(
        Uri.parse("$apiBaseUrl/api/analyze"),
        headers: {"Content-Type": "application/json"},
        body: jsonEncode({"message": message}),
      );

      if (response.statusCode == 200) {
        setState(() {
          _result = jsonDecode(response.body);
        });
      } else {
        setState(() {
          _error = "Server error: ${response.statusCode}";
        });
      }
    } catch (e) {
      setState(() {
        _error = "Could not reach server. Is the API running?\n$e";
      });
    } finally {
      setState(() {
        _loading = false;
      });
    }
  }

  Color _riskColor(double score) {
    if (score >= 75) return const Color(0xFF8B2C2C);
    if (score >= 40) return const Color(0xFF8B6B2C);
    return const Color(0xFF2C8B45);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text("Phishing & Deepfake Detector"),
        backgroundColor: const Color(0xFF1A1D23),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const Text(
              "Paste a suspicious email or message below to check its risk score.",
              style: TextStyle(color: Colors.grey, fontSize: 14),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _controller,
              maxLines: 8,
              style: const TextStyle(color: Colors.white),
              decoration: InputDecoration(
                hintText: "Paste message text here...",
                hintStyle: const TextStyle(color: Colors.grey),
                filled: true,
                fillColor: const Color(0xFF1A1D23),
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(10),
                  borderSide: BorderSide.none,
                ),
              ),
            ),
            const SizedBox(height: 12),
            ElevatedButton(
              onPressed: _loading ? null : _analyzeMessage,
              style: ElevatedButton.styleFrom(
                backgroundColor: const Color(0xFF4F8CFF),
                padding: const EdgeInsets.symmetric(vertical: 14),
              ),
              child: _loading
                  ? const SizedBox(
                      height: 20,
                      width: 20,
                      child: CircularProgressIndicator(
                          color: Colors.white, strokeWidth: 2),
                    )
                  : const Text("Analyze", style: TextStyle(fontSize: 16)),
            ),
            const SizedBox(height: 20),
            if (_error != null)
              Container(
                padding: const EdgeInsets.all(14),
                decoration: BoxDecoration(
                  color: const Color(0xFF3A1414),
                  borderRadius: BorderRadius.circular(10),
                ),
                child: Text(_error!, style: const TextStyle(color: Colors.white)),
              ),
            if (_result != null) _buildResultCard(),
          ],
        ),
      ),
    );
  }

  Widget _buildResultCard() {
    final double score = (_result!["risk_score"] as num).toDouble();
    final String verdict = _result!["verdict"];
    final List urgency = _result!["flagged_urgency_words"] ?? [];
    final List authority = _result!["flagged_authority_words"] ?? [];
    final List financial = _result!["flagged_financial_words"] ?? [];

    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: _riskColor(score).withOpacity(0.25),
        border: Border.all(color: _riskColor(score)),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            "${score.toStringAsFixed(1)}% Risk",
            style: const TextStyle(
                fontSize: 28, fontWeight: FontWeight.bold, color: Colors.white),
          ),
          const SizedBox(height: 6),
          Text(verdict, style: const TextStyle(color: Colors.white70)),
          const SizedBox(height: 12),
          if (urgency.isNotEmpty) _buildFlagRow("Urgency signals", urgency),
          if (authority.isNotEmpty) _buildFlagRow("Authority signals", authority),
          if (financial.isNotEmpty) _buildFlagRow("Financial signals", financial),
          const SizedBox(height: 6),
          Text(
            "URLs: ${_result!["url_count"]}  |  "
            "Exclamations: ${_result!["exclamation_count"]}  |  "
            "Sentence uniformity: ${_result!["burstiness"]}",
            style: const TextStyle(color: Colors.white54, fontSize: 12),
          ),
        ],
      ),
    );
  }

  Widget _buildFlagRow(String label, List words) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Wrap(
        crossAxisAlignment: WrapCrossAlignment.center,
        spacing: 6,
        runSpacing: 4,
        children: [
          Text("$label:",
              style: const TextStyle(
                  color: Colors.white70, fontWeight: FontWeight.bold, fontSize: 12)),
          ...words.map((w) => Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                decoration: BoxDecoration(
                  color: const Color(0xFF2A2D33),
                  borderRadius: BorderRadius.circular(6),
                ),
                child: Text(w.toString(),
                    style: const TextStyle(color: Colors.white, fontSize: 12)),
              )),
        ],
      ),
    );
  }
}
