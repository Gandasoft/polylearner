import 'package:flutter/material.dart';
import '../theme/app_theme.dart';

class NewTaskScreen extends StatefulWidget {
  const NewTaskScreen({super.key});

  @override
  State<NewTaskScreen> createState() => _NewTaskScreenState();
}

class _NewTaskScreenState extends State<NewTaskScreen> {
  final TextEditingController _taskController = TextEditingController();
  final TextEditingController _notesController = TextEditingController();
  String _selectedProject = 'Inbox';
  String _selectedDuration = '1h';
  bool _isUrgent = false;
  DateTime _dueDate = DateTime.now().add(const Duration(days: 1));

  @override
  void dispose() {
    _taskController.dispose();
    _notesController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.darkBackground,
      appBar: AppBar(
        backgroundColor: AppTheme.darkBackground,
        leading: IconButton(
          icon: const Icon(Icons.close, color: AppTheme.textPrimary),
          onPressed: () => Navigator.pop(context),
        ),
        title: const Text('New Task'),
        actions: [
          Padding(
            padding: const EdgeInsets.only(right: 16),
            child: ElevatedButton(
              onPressed: _saveTask,
              style: ElevatedButton.styleFrom(
                padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 10),
              ),
              child: const Text('Save'),
            ),
          ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _buildTaskInput(),
            const SizedBox(height: 24),
            _buildAISuggestion(),
            const SizedBox(height: 24),
            _buildQuickOptions(),
            const SizedBox(height: 24),
            _buildDetails(),
            const SizedBox(height: 24),
            _buildNotes(),
            const SizedBox(height: 24),
            _buildActionBar(),
          ],
        ),
      ),
    );
  }

  Widget _buildTaskInput() {
    return TextField(
      controller: _taskController,
      style: const TextStyle(
        color: AppTheme.textPrimary,
        fontSize: 18,
        fontWeight: FontWeight.w500,
      ),
      decoration: InputDecoration(
        hintText: 'What needs to be done?',
        hintStyle: TextStyle(
          color: AppTheme.textSecondary.withOpacity(0.5),
          fontSize: 18,
        ),
        border: InputBorder.none,
        contentPadding: EdgeInsets.zero,
      ),
      maxLines: null,
      autofocus: true,
    );
  }

  Widget _buildAISuggestion() {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppTheme.primaryBlue.withOpacity(0.1),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
          color: AppTheme.primaryBlue.withOpacity(0.3),
          width: 1,
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(
                Icons.auto_awesome,
                color: AppTheme.primaryBlue,
                size: 16,
              ),
              const SizedBox(width: 8),
              Text(
                'AI SUGGESTION',
                style: TextStyle(
                  color: AppTheme.primaryBlue,
                  fontSize: 11,
                  fontWeight: FontWeight.w600,
                  letterSpacing: 1.2,
                ),
              ),
              const Spacer(),
              IconButton(
                icon: Icon(
                  Icons.close,
                  color: AppTheme.primaryBlue,
                  size: 18,
                ),
                onPressed: () {},
                padding: EdgeInsets.zero,
                constraints: const BoxConstraints(),
              ),
            ],
          ),
          const SizedBox(height: 12),
          RichText(
            text: TextSpan(
              style: const TextStyle(
                color: AppTheme.textPrimary,
                fontSize: 14,
                height: 1.4,
              ),
              children: [
                const TextSpan(text: 'Based on "Financial Report", I\'ve set the project to '),
                TextSpan(
                  text: 'Finance Q3',
                  style: TextStyle(
                    color: AppTheme.primaryBlue,
                    fontWeight: FontWeight.w600,
                  ),
                ),
                const TextSpan(text: ' and prioritized it as '),
                TextSpan(
                  text: 'High',
                  style: TextStyle(
                    color: AppTheme.error,
                    fontWeight: FontWeight.w600,
                  ),
                ),
                const TextSpan(text: '.'),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildQuickOptions() {
    return Wrap(
      spacing: 12,
      runSpacing: 12,
      children: [
        _buildOptionChip(
          icon: Icons.calendar_today,
          label: 'Today',
          onTap: () => _selectDate(context),
        ),
        _buildOptionChip(
          icon: Icons.schedule,
          label: '15m',
          isSelected: _selectedDuration == '15m',
          onTap: () => setState(() => _selectedDuration = '15m'),
        ),
        _buildOptionChip(
          icon: Icons.flag,
          label: 'Urgent',
          isSelected: _isUrgent,
          color: _isUrgent ? AppTheme.error : null,
          onTap: () => setState(() => _isUrgent = !_isUrgent),
        ),
        _buildOptionChip(
          icon: Icons.person_add,
          label: 'Assign',
          onTap: () {},
        ),
      ],
    );
  }

  Widget _buildOptionChip({
    required IconData icon,
    required String label,
    bool isSelected = false,
    Color? color,
    required VoidCallback onTap,
  }) {
    final chipColor = color ?? (isSelected ? AppTheme.primaryBlue : AppTheme.cardBackground);
    
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(8),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
        decoration: BoxDecoration(
          color: isSelected || color != null 
              ? chipColor.withOpacity(0.2) 
              : chipColor,
          borderRadius: BorderRadius.circular(8),
          border: Border.all(
            color: isSelected || color != null 
                ? chipColor.withOpacity(0.5) 
                : Colors.transparent,
            width: 1,
          ),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(
              icon,
              color: isSelected || color != null ? chipColor : AppTheme.textSecondary,
              size: 16,
            ),
            const SizedBox(width: 8),
            Text(
              label,
              style: TextStyle(
                color: isSelected || color != null ? chipColor : AppTheme.textPrimary,
                fontSize: 14,
                fontWeight: FontWeight.w500,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildDetails() {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppTheme.cardBackground,
        borderRadius: BorderRadius.circular(12),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'DETAILS',
            style: TextStyle(
              color: AppTheme.textSecondary,
              fontSize: 11,
              fontWeight: FontWeight.w600,
              letterSpacing: 1.2,
            ),
          ),
          const SizedBox(height: 16),
          _buildDetailRow(
            icon: Icons.event,
            label: 'Due Date',
            value: 'Tomorrow, 5:00 PM',
            onTap: () => _selectDate(context),
          ),
          const SizedBox(height: 16),
          _buildDetailRow(
            icon: Icons.folder,
            label: 'Project',
            value: _selectedProject,
            onTap: () => _selectProject(context),
          ),
          const SizedBox(height: 16),
          _buildDetailRow(
            icon: Icons.schedule,
            label: 'Duration',
            value: _selectedDuration,
            onTap: () => _selectDuration(context),
          ),
        ],
      ),
    );
  }

  Widget _buildDetailRow({
    required IconData icon,
    required String label,
    required String value,
    required VoidCallback onTap,
  }) {
    return InkWell(
      onTap: onTap,
      child: Row(
        children: [
          Icon(icon, color: AppTheme.textSecondary, size: 20),
          const SizedBox(width: 16),
          Expanded(
            child: Text(
              label,
              style: const TextStyle(
                color: AppTheme.textPrimary,
                fontSize: 15,
              ),
            ),
          ),
          Text(
            value,
            style: TextStyle(
              color: AppTheme.textSecondary,
              fontSize: 14,
            ),
          ),
          const SizedBox(width: 8),
          Icon(
            Icons.chevron_right,
            color: AppTheme.textSecondary,
            size: 20,
          ),
        ],
      ),
    );
  }

  Widget _buildNotes() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Notes',
          style: TextStyle(
            color: AppTheme.textSecondary,
            fontSize: 15,
            fontWeight: FontWeight.w600,
          ),
        ),
        const SizedBox(height: 12),
        TextField(
          controller: _notesController,
          style: const TextStyle(
            color: AppTheme.textPrimary,
            fontSize: 15,
          ),
          decoration: InputDecoration(
            hintText: 'Add extra details, subtasks, or links...',
            hintStyle: TextStyle(
              color: AppTheme.textSecondary.withOpacity(0.5),
              fontSize: 15,
            ),
            border: OutlineInputBorder(
              borderRadius: BorderRadius.circular(12),
              borderSide: BorderSide(
                color: AppTheme.cardBackground,
                width: 1,
              ),
            ),
            enabledBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(12),
              borderSide: BorderSide(
                color: AppTheme.cardBackground,
                width: 1,
              ),
            ),
            focusedBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(12),
              borderSide: BorderSide(
                color: AppTheme.primaryBlue.withOpacity(0.5),
                width: 1,
              ),
            ),
            filled: true,
            fillColor: AppTheme.cardBackground,
            contentPadding: const EdgeInsets.all(16),
          ),
          maxLines: 4,
        ),
      ],
    );
  }

  Widget _buildActionBar() {
    return Container(
      padding: const EdgeInsets.symmetric(vertical: 12),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          IconButton(
            icon: const Icon(Icons.alternate_email, color: AppTheme.textSecondary),
            onPressed: () {},
          ),
          IconButton(
            icon: const Icon(Icons.tag, color: AppTheme.textSecondary),
            onPressed: () {},
          ),
          IconButton(
            icon: const Icon(Icons.link, color: AppTheme.textSecondary),
            onPressed: () {},
          ),
          IconButton(
            icon: const Icon(Icons.camera_alt, color: AppTheme.textSecondary),
            onPressed: () {},
          ),
          IconButton(
            icon: const Icon(Icons.mic, color: AppTheme.textSecondary),
            onPressed: () {},
          ),
          const Spacer(),
          IconButton(
            icon: const Icon(Icons.arrow_upward, color: AppTheme.primaryBlue),
            onPressed: _saveTask,
            style: IconButton.styleFrom(
              backgroundColor: AppTheme.primaryBlue.withOpacity(0.2),
            ),
          ),
        ],
      ),
    );
  }

  Future<void> _selectDate(BuildContext context) async {
    final DateTime? picked = await showDatePicker(
      context: context,
      initialDate: _dueDate,
      firstDate: DateTime.now(),
      lastDate: DateTime.now().add(const Duration(days: 365)),
      builder: (context, child) {
        return Theme(
          data: Theme.of(context).copyWith(
            colorScheme: const ColorScheme.dark(
              primary: AppTheme.primaryBlue,
              surface: AppTheme.cardBackground,
            ),
          ),
          child: child!,
        );
      },
    );
    if (picked != null && picked != _dueDate) {
      setState(() {
        _dueDate = picked;
      });
    }
  }

  void _selectProject(BuildContext context) {
    showModalBottomSheet(
      context: context,
      backgroundColor: AppTheme.cardBackground,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (context) {
        return Container(
          padding: const EdgeInsets.all(20),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              ListTile(
                title: const Text('Inbox', style: TextStyle(color: AppTheme.textPrimary)),
                onTap: () {
                  setState(() => _selectedProject = 'Inbox');
                  Navigator.pop(context);
                },
              ),
              ListTile(
                title: const Text('Finance Q3', style: TextStyle(color: AppTheme.textPrimary)),
                onTap: () {
                  setState(() => _selectedProject = 'Finance Q3');
                  Navigator.pop(context);
                },
              ),
              ListTile(
                title: const Text('Design', style: TextStyle(color: AppTheme.textPrimary)),
                onTap: () {
                  setState(() => _selectedProject = 'Design');
                  Navigator.pop(context);
                },
              ),
            ],
          ),
        );
      },
    );
  }

  void _selectDuration(BuildContext context) {
    showModalBottomSheet(
      context: context,
      backgroundColor: AppTheme.cardBackground,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (context) {
        return Container(
          padding: const EdgeInsets.all(20),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: ['15m', '30m', '1h', '2h', '4h'].map((duration) {
              return ListTile(
                title: Text(duration, style: const TextStyle(color: AppTheme.textPrimary)),
                onTap: () {
                  setState(() => _selectedDuration = duration);
                  Navigator.pop(context);
                },
              );
            }).toList(),
          ),
        );
      },
    );
  }

  void _saveTask() {
    if (_taskController.text.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Please enter a task'),
          backgroundColor: AppTheme.error,
        ),
      );
      return;
    }
    
    // TODO: Implement task saving logic
    Navigator.pop(context);
    
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text('Task created successfully'),
        backgroundColor: AppTheme.success,
      ),
    );
  }
}
