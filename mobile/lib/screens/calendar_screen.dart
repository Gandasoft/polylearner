import 'package:flutter/material.dart';
import 'package:table_calendar/table_calendar.dart';
import 'package:intl/intl.dart';
import '../theme/app_theme.dart';
import 'new_task_screen.dart';

class CalendarScreen extends StatefulWidget {
  const CalendarScreen({super.key});

  @override
  State<CalendarScreen> createState() => _CalendarScreenState();
}

class _CalendarScreenState extends State<CalendarScreen> {
  DateTime _focusedDay = DateTime.now();
  DateTime? _selectedDay;
  CalendarFormat _calendarFormat = CalendarFormat.week;

  final Map<DateTime, List<CalendarEvent>> _events = {
    DateTime(2024, 10, 24, 9, 0): [
      CalendarEvent(
        title: 'Q4 Strategy Deep Work',
        time: '09:00 - 10:30',
        description: 'Review quarterly goals and revenue...',
        type: 'HIGH FOCUS',
        duration: '2H 30M',
      ),
    ],
    DateTime(2024, 10, 24, 11, 30): [
      CalendarEvent(
        title: 'Admin Batch',
        time: '11:30',
        description: 'Low cognitive load',
        duration: '45m',
        tasks: ['Clear Inbox (Zero)', 'Reply to Team on Slack'],
      ),
    ],
    DateTime(2024, 10, 24, 13, 0): [
      CalendarEvent(
        title: 'Client Review: Acme Corp',
        time: '01:00 PM',
        description: 'Google Meet',
        duration: '1h',
        hasVideoCall: true,
      ),
    ],
  };

  @override
  void initState() {
    super.initState();
    _selectedDay = _focusedDay;
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.darkBackground,
      appBar: AppBar(
        backgroundColor: AppTheme.darkBackground,
        title: Text(
          DateFormat('MMMM dd').format(_selectedDay ?? _focusedDay),
          style: const TextStyle(
            color: AppTheme.textPrimary,
            fontSize: 20,
            fontWeight: FontWeight.bold,
          ),
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.ios_share, color: AppTheme.textPrimary),
            onPressed: () {},
          ),
          IconButton(
            icon: const Icon(Icons.refresh, color: AppTheme.primaryBlue),
            onPressed: () {},
          ),
        ],
      ),
      body: Column(
        children: [
          _buildCalendar(),
          Expanded(
            child: _buildEventsList(),
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () {
          Navigator.push(
            context,
            MaterialPageRoute(builder: (context) => const NewTaskScreen()),
          );
        },
        backgroundColor: AppTheme.primaryBlue,
        child: const Icon(Icons.add),
      ),
    );
  }

  Widget _buildCalendar() {
    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 20, vertical: 10),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppTheme.cardBackground,
        borderRadius: BorderRadius.circular(16),
      ),
      child: TableCalendar(
        firstDay: DateTime.utc(2024, 1, 1),
        lastDay: DateTime.utc(2025, 12, 31),
        focusedDay: _focusedDay,
        selectedDayPredicate: (day) => isSameDay(_selectedDay, day),
        calendarFormat: _calendarFormat,
        startingDayOfWeek: StartingDayOfWeek.monday,
        onDaySelected: (selectedDay, focusedDay) {
          setState(() {
            _selectedDay = selectedDay;
            _focusedDay = focusedDay;
          });
        },
        onFormatChanged: (format) {
          setState(() {
            _calendarFormat = format;
          });
        },
        onPageChanged: (focusedDay) {
          _focusedDay = focusedDay;
        },
        eventLoader: (day) {
          return _events[DateTime(day.year, day.month, day.day)] ?? [];
        },
        calendarStyle: CalendarStyle(
          defaultTextStyle: const TextStyle(color: AppTheme.textPrimary),
          weekendTextStyle: const TextStyle(color: AppTheme.textPrimary),
          outsideTextStyle: TextStyle(color: AppTheme.textSecondary.withOpacity(0.3)),
          selectedDecoration: const BoxDecoration(
            color: AppTheme.primaryBlue,
            shape: BoxShape.circle,
          ),
          todayDecoration: BoxDecoration(
            color: AppTheme.primaryBlue.withOpacity(0.3),
            shape: BoxShape.circle,
          ),
          markerDecoration: const BoxDecoration(
            color: AppTheme.primaryBlue,
            shape: BoxShape.circle,
          ),
          selectedTextStyle: const TextStyle(color: Colors.white),
          todayTextStyle: const TextStyle(color: AppTheme.textPrimary),
          cellMargin: const EdgeInsets.all(6),
        ),
        headerStyle: HeaderStyle(
          formatButtonVisible: false,
          titleCentered: true,
          titleTextStyle: const TextStyle(
            color: AppTheme.textPrimary,
            fontSize: 16,
            fontWeight: FontWeight.w600,
          ),
          leftChevronIcon: const Icon(Icons.chevron_left, color: AppTheme.textPrimary),
          rightChevronIcon: const Icon(Icons.chevron_right, color: AppTheme.textPrimary),
        ),
        daysOfWeekStyle: DaysOfWeekStyle(
          weekdayStyle: TextStyle(
            color: AppTheme.textSecondary,
            fontSize: 12,
            fontWeight: FontWeight.w600,
          ),
          weekendStyle: TextStyle(
            color: AppTheme.textSecondary,
            fontSize: 12,
            fontWeight: FontWeight.w600,
          ),
        ),
      ),
    );
  }

  Widget _buildEventsList() {
    final selectedEvents = _getEventsForDay(_selectedDay ?? _focusedDay);

    return ListView(
      padding: const EdgeInsets.all(20),
      children: [
        _buildTimeSlot('09:00\nAM', selectedEvents.isNotEmpty ? selectedEvents[0] : null),
        const SizedBox(height: 16),
        _buildTimeSlot('10:42\nAM', null, showCurrentTimeLine: true),
        const SizedBox(height: 16),
        _buildTimeSlot('11:30\nAM', selectedEvents.length > 1 ? selectedEvents[1] : null),
        const SizedBox(height: 16),
        _buildLunchBreak(),
        const SizedBox(height: 16),
        _buildTimeSlot('01:00\nPM', selectedEvents.length > 2 ? selectedEvents[2] : null),
        const SizedBox(height: 16),
        _buildTimeSlot('03:00\nAM', null, hasSuggestion: true),
      ],
    );
  }

  List<CalendarEvent> _getEventsForDay(DateTime day) {
    return _events.entries
        .where((entry) =>
            entry.key.year == day.year &&
            entry.key.month == day.month &&
            entry.key.day == day.day)
        .expand((entry) => entry.value)
        .toList();
  }

  Widget _buildTimeSlot(String time, CalendarEvent? event,
      {bool showCurrentTimeLine = false, bool hasSuggestion = false}) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        SizedBox(
          width: 60,
          child: Text(
            time,
            style: TextStyle(
              color: showCurrentTimeLine ? AppTheme.primaryBlue : AppTheme.textSecondary,
              fontSize: 12,
              fontWeight: FontWeight.w600,
            ),
          ),
        ),
        const SizedBox(width: 16),
        Expanded(
          child: Column(
            children: [
              if (showCurrentTimeLine)
                Row(
                  children: [
                    Container(
                      width: 8,
                      height: 8,
                      decoration: const BoxDecoration(
                        color: AppTheme.primaryBlue,
                        shape: BoxShape.circle,
                      ),
                    ),
                    Expanded(
                      child: Container(
                        height: 2,
                        color: AppTheme.primaryBlue,
                      ),
                    ),
                  ],
                ),
              if (event != null) _buildEventCard(event),
              if (hasSuggestion) _buildSuggestionCard(),
            ],
          ),
        ),
      ],
    );
  }

  Widget _buildEventCard(CalendarEvent event) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppTheme.cardBackground,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
          color: event.type == 'HIGH FOCUS'
              ? AppTheme.primaryBlue.withOpacity(0.3)
              : Colors.transparent,
          width: 1,
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (event.type != null)
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
              margin: const EdgeInsets.only(bottom: 12),
              decoration: BoxDecoration(
                color: AppTheme.primaryBlue.withOpacity(0.2),
                borderRadius: BorderRadius.circular(6),
              ),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(Icons.brightness_high, color: AppTheme.primaryBlue, size: 12),
                  const SizedBox(width: 6),
                  Text(
                    event.type!,
                    style: TextStyle(
                      color: AppTheme.primaryBlue,
                      fontSize: 10,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                  const SizedBox(width: 6),
                  Text(
                    event.duration,
                    style: TextStyle(
                      color: AppTheme.primaryBlue,
                      fontSize: 10,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ],
              ),
            ),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Expanded(
                child: Text(
                  event.title,
                  style: const TextStyle(
                    color: AppTheme.textPrimary,
                    fontSize: 16,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ),
              if (event.hasVideoCall)
                Icon(Icons.videocam, color: AppTheme.textSecondary, size: 20),
              if (event.type == 'HIGH FOCUS')
                ElevatedButton.icon(
                  onPressed: () {},
                  icon: const Icon(Icons.play_arrow, size: 16),
                  label: const Text('Start Focus'),
                  style: ElevatedButton.styleFrom(
                    padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                  ),
                ),
            ],
          ),
          const SizedBox(height: 8),
          Text(
            event.description,
            style: TextStyle(
              color: AppTheme.textSecondary,
              fontSize: 13,
            ),
          ),
          if (event.tasks != null && event.tasks!.isNotEmpty) ...[
            const SizedBox(height: 16),
            ...event.tasks!.map((task) => Padding(
                  padding: const EdgeInsets.only(bottom: 8),
                  child: Row(
                    children: [
                      Container(
                        width: 20,
                        height: 20,
                        decoration: BoxDecoration(
                          color: AppTheme.darkBackground,
                          borderRadius: BorderRadius.circular(4),
                        ),
                        child: const Icon(
                          Icons.check_box_outline_blank,
                          color: AppTheme.textSecondary,
                          size: 14,
                        ),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Text(
                          task,
                          style: const TextStyle(
                            color: AppTheme.textPrimary,
                            fontSize: 14,
                          ),
                        ),
                      ),
                    ],
                  ),
                )),
          ],
        ],
      ),
    );
  }

  Widget _buildSuggestionCard() {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppTheme.cardBackground.withOpacity(0.5),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
          color: AppTheme.primaryBlue.withOpacity(0.2),
          width: 1,
          style: BorderStyle.solid,
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(Icons.auto_awesome, color: AppTheme.primaryBlue, size: 16),
              const SizedBox(width: 8),
              Text(
                'Suggestion',
                style: TextStyle(
                  color: AppTheme.primaryBlue,
                  fontSize: 12,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Text(
            'Move "Admin Batch" to 4 PM to extend Deep Work flow?',
            style: TextStyle(
              color: AppTheme.textPrimary,
              fontSize: 14,
            ),
          ),
          const SizedBox(height: 12),
          Row(
            children: [
              TextButton(
                onPressed: () {},
                child: Text(
                  'Apply',
                  style: TextStyle(color: AppTheme.primaryBlue),
                ),
              ),
              TextButton(
                onPressed: () {},
                child: Text(
                  'Dismiss',
                  style: TextStyle(color: AppTheme.textSecondary),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildLunchBreak() {
    return Row(
      children: [
        const SizedBox(width: 76),
        Expanded(
          child: Container(
            padding: const EdgeInsets.symmetric(vertical: 8),
            child: Row(
              children: [
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                  decoration: BoxDecoration(
                    color: AppTheme.cardBackground.withOpacity(0.5),
                    borderRadius: BorderRadius.circular(6),
                  ),
                  child: Text(
                    'Lunch Break',
                    style: TextStyle(
                      color: AppTheme.textSecondary,
                      fontSize: 13,
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),
      ],
    );
  }
}

class CalendarEvent {
  final String title;
  final String time;
  final String description;
  final String? type;
  final String duration;
  final List<String>? tasks;
  final bool hasVideoCall;

  CalendarEvent({
    required this.title,
    required this.time,
    required this.description,
    this.type,
    required this.duration,
    this.tasks,
    this.hasVideoCall = false,
  });
}
