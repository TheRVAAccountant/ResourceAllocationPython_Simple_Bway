# /ra-feature-dev

Complete feature development workflow for Resource Management System with automated agent coordination.

## Usage
```
/ra-feature-dev <feature_description> [--priority=<high|medium|low>] [--include-gui] [--include-excel] [--include-tests]
```

## Workflow Process

### Phase 1: Requirements Analysis (5-10 minutes)
- **resource-allocation-expert**: Analyze feature requirements and business impact
- Define acceptance criteria and success metrics
- Identify potential conflicts with existing allocation logic
- Create technical specification and implementation approach

### Phase 2: Implementation Planning (10-15 minutes)
- **resource-allocation-expert**: Design business logic and algorithm changes
- **excel-integration-specialist**: Plan Excel integration requirements (if needed)
- **gui-ux-specialist**: Design user interface changes (if needed)
- Create detailed implementation plan with dependencies

### Phase 3: Core Development (30-60 minutes)
- **resource-allocation-expert**: Implement business logic and allocation algorithms
- **excel-integration-specialist**: Implement Excel processing changes
- **gui-ux-specialist**: Create/update user interface components
- Coordinate integration between components

### Phase 4: Testing & Quality Assurance (20-30 minutes)
- **testing-qa-specialist**: Create comprehensive test suite for new feature
- Run integration tests with existing system
- Validate business logic with edge cases
- Test Excel workflows and GUI interactions

### Phase 5: Performance Optimization (10-20 minutes)
- **performance-optimization-specialist**: Analyze performance impact
- Optimize critical paths and memory usage
- Validate scalability with large datasets
- Implement monitoring for new feature

### Phase 6: Deployment Preparation (10-15 minutes)
- **deployment-devops-specialist**: Update deployment procedures
- Create rollback plans and monitoring alerts
- Update documentation and operational procedures
- Prepare user communication and training materials

## Agent Coordination Pattern
```
resource-allocation-expert (lead) →
├── excel-integration-specialist (if Excel changes needed)
├── gui-ux-specialist (if UI changes needed)
└── coordination with:
    ├── testing-qa-specialist (validation)
    ├── performance-optimization-specialist (optimization)
    └── deployment-devops-specialist (deployment)
```

## Examples
- `/ra-feature-dev Add priority boost for emergency routes --priority=high --include-gui --include-tests`
- `/ra-feature-dev Implement vehicle maintenance scheduling integration --include-excel --include-tests`
- `/ra-feature-dev Create driver performance analytics dashboard --include-gui --priority=medium`

## Quality Gates
- ✅ Business logic validation with domain expert review
- ✅ Excel integration testing with template compliance
- ✅ GUI usability testing and user experience validation
- ✅ Comprehensive test coverage (>95% for new code)
- ✅ Performance benchmarking and optimization
- ✅ Deployment readiness and rollback procedures

## Deliverables
- Production-ready feature implementation
- Comprehensive test suite with >95% coverage
- Updated documentation and user guides
- Performance analysis and optimization recommendations
- Deployment plan with rollback procedures
- User training materials and operational procedures
