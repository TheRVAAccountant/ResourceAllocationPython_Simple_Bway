# Resource Management System - Agent Usage Guide

## Quick Start Examples

### 1. Feature Development
```bash
# Develop a new priority system for emergency routes
claude "Use resource-allocation-expert to design and implement emergency route priority system with GUI controls"

# Add vehicle maintenance scheduling
claude "/ra-feature-dev Implement vehicle maintenance scheduling integration --include-excel --include-gui --priority=high"
```

### 2. Excel Integration Tasks
```bash
# Fix Excel template compliance issues
claude "Use excel-integration-specialist to analyze and fix Daily Summary Log template compliance issues"

# Optimize large file processing
claude "Have excel-integration-specialist optimize the 3-file Excel workflow for better memory usage and performance"
```

### 3. GUI Improvements
```bash
# Enhance user experience for allocation workflow
claude "Use gui-ux-specialist to redesign the allocation tab for better user experience and progress tracking"

# Add dashboard analytics
claude "Have gui-ux-specialist create a real-time analytics dashboard showing allocation metrics and trends"
```

### 4. Testing & Quality Assurance
```bash
# Create comprehensive test suite
claude "Use testing-qa-specialist to create integration tests for the complete 3-file Excel allocation workflow"

# Add performance regression tests
claude "Have testing-qa-specialist implement performance benchmarking and regression testing for large datasets"
```

### 5. Performance Optimization
```bash
# Optimize allocation algorithm performance
claude "/ra-optimize --target=allocation-algorithm --metric=speed --profile"

# Memory usage optimization
claude "Use performance-optimization-specialist to analyze and optimize memory usage for processing 1000+ routes"
```

### 6. Bug Fixing & Debugging
```bash
# Debug Excel parsing errors
claude "/ra-debug-fix Excel file validation failing intermittently --error-log=logs/excel_error.log --severity=high"

# Fix GUI freezing issues
claude "Use gui-ux-specialist and performance-optimization-specialist to resolve GUI freezing during large allocations"
```

### 7. Deployment & Operations
```bash
# Prepare production deployment
claude "Use deployment-devops-specialist to create deployment procedures and monitoring for production release"

# Set up CI/CD pipeline
claude "Have deployment-devops-specialist implement automated testing and deployment pipeline with quality gates"
```

### 8. Complex Multi-Agent Tasks
```bash
# Major feature with full coordination
claude "/ra-orchestrate 'Build machine learning-powered route optimization system' --scope=feature --timeline=release --include-all-agents"

# System architecture improvements
claude "/ra-orchestrate 'Implement microservices architecture for better scalability' --scope=system --timeline=major"
```

## Agent Specialization Summary

| Agent | Primary Focus | When to Use |
|-------|---------------|-------------|
| **resource-allocation-expert** | Business logic, algorithms, domain expertise | Core allocation logic, business rules, domain problems |
| **excel-integration-specialist** | Excel processing, template compliance, data formatting | Excel file issues, performance, template problems |
| **gui-ux-specialist** | User interface, user experience, CustomTkinter | GUI improvements, user workflow, interface design |
| **testing-qa-specialist** | Testing, quality assurance, bug prevention | Test creation, quality issues, regression prevention |
| **performance-optimization-specialist** | Performance tuning, memory optimization, scalability | Speed issues, memory problems, scalability concerns |
| **deployment-devops-specialist** | Deployment, monitoring, production operations | Production deployment, monitoring, operational issues |

## Best Practices

### Single Agent Tasks
- Use specific agents for focused tasks in their domain
- Provide clear context about the current issue or requirement
- Include relevant error logs, performance metrics, or user feedback

### Multi-Agent Coordination
- Use `/ra-orchestrate` for complex tasks requiring multiple specializations
- Use `/ra-feature-dev` for complete feature development workflows
- Use `/ra-debug-fix` for comprehensive problem resolution

### Context Sharing
- Reference existing files and code when asking for modifications
- Provide business context and user impact information
- Include performance requirements and constraints

### Quality Assurance
- Always include testing requirements in feature development
- Request performance analysis for any significant changes
- Ensure deployment procedures are updated for major changes

## Success Tips

1. **Be Specific**: Provide detailed requirements and context
2. **Think Holistically**: Consider impact across all system components
3. **Prioritize Quality**: Include testing and documentation requirements
4. **Consider Users**: Always think about operational impact and user experience
5. **Plan for Scale**: Consider performance and scalability implications
6. **Document Everything**: Ensure changes are well-documented and maintainable

## Common Workflows

### Weekly Development Sprint
```bash
# Plan and execute weekly improvements
claude "/ra-orchestrate 'Weekly sprint: improve allocation speed and add driver analytics' --scope=integration --timeline=sprint"
```

### Production Issue Response
```bash
# Handle critical production problems
claude "/ra-debug-fix Production allocation failures affecting morning operations --severity=critical --reproduce-steps='Load morning routes, run allocation, system crashes'"
```

### Quality Improvement Cycle
```bash
# Regular quality improvements
claude "Use testing-qa-specialist and performance-optimization-specialist to identify and fix technical debt in the allocation engine"
```

### User Experience Enhancement
```bash
# Improve daily operator experience
claude "Use gui-ux-specialist and resource-allocation-expert to simplify the daily allocation workflow and reduce user training time"
```

Remember: These agents are designed to work together seamlessly. Don't hesitate to use multiple agents for complex tasks, and always consider the broader impact of changes on the entire system.
