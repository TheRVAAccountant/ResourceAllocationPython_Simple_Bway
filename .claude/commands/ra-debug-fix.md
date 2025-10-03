# /ra-debug-fix

Comprehensive bug analysis and resolution workflow with root cause analysis and prevention.

## Usage
```
/ra-debug-fix <issue_description> [--error-log=<file>] [--reproduce-steps=<steps>] [--severity=<critical|high|medium|low>]
```

## Debugging Process

### Phase 1: Issue Analysis (10-15 minutes)
- **resource-allocation-expert**: Analyze business impact and operational consequences
- **testing-qa-specialist**: Review error logs and reproduce the issue
- Identify affected components and potential root causes
- Assess urgency and impact on production operations

### Phase 2: Root Cause Investigation (15-30 minutes)
- **Coordinator Agent**: Route to appropriate specialist based on error type:
  - **excel-integration-specialist**: Excel file processing errors, template issues
  - **gui-ux-specialist**: GUI crashes, user interaction problems
  - **performance-optimization-specialist**: Memory leaks, performance degradation
  - **deployment-devops-specialist**: Environment or configuration issues

### Phase 3: Solution Development (20-45 minutes)
- Primary specialist implements the fix with comprehensive error handling
- **resource-allocation-expert**: Validate business logic integrity
- **testing-qa-specialist**: Create regression tests to prevent future occurrences
- Document the fix and lessons learned

### Phase 4: Validation & Testing (15-25 minutes)
- **testing-qa-specialist**: Run comprehensive regression tests
- Validate fix doesn't introduce new issues
- Test edge cases and boundary conditions
- Performance impact assessment

### Phase 5: Deployment & Monitoring (10-15 minutes)
- **deployment-devops-specialist**: Deploy fix with monitoring
- Set up alerts for similar issues
- Update operational procedures and documentation
- Communicate resolution to stakeholders

## Issue Routing Logic

### Excel-Related Issues
- File parsing errors, template compliance issues
- Data format problems, Excel crashes
- Route to: **excel-integration-specialist**

### GUI-Related Issues  
- Application crashes, UI freezing, user interaction problems
- Display issues, responsive design problems
- Route to: **gui-ux-specialist**

### Performance Issues
- Memory leaks, slow processing, resource exhaustion
- Algorithm inefficiencies, scaling problems
- Route to: **performance-optimization-specialist**

### Business Logic Issues
- Incorrect allocations, rule violations, data inconsistencies
- Algorithm bugs, edge case handling
- Route to: **resource-allocation-expert**

### Environment/Deployment Issues
- Configuration problems, dependency conflicts, deployment failures
- Route to: **deployment-devops-specialist**

## Quality Assurance Process
1. **Reproduce**: Confirm the issue can be reproduced consistently
2. **Isolate**: Identify the minimum reproduction case
3. **Analyze**: Understand root cause and contributing factors
4. **Fix**: Implement robust solution with proper error handling
5. **Test**: Validate fix and prevent regressions
6. **Document**: Update code comments and operational procedures
7. **Monitor**: Track metrics to ensure resolution effectiveness

## Examples
- `/ra-debug-fix Excel file validation failing for Daily Summary Log --error-log=logs/excel_error.log --severity=high`
- `/ra-debug-fix GUI freezing during large allocation runs --reproduce-steps="1. Load 1000+ routes 2. Run allocation" --severity=critical`
- `/ra-debug-fix Memory usage growing during repeated allocations --severity=medium`

## Emergency Response (Critical Issues)
For critical production issues:
1. **Immediate Assessment**: Resource allocation expert triages impact
2. **Parallel Investigation**: Multiple agents investigate simultaneously
3. **Hotfix Development**: Rapid implementation with minimal testing
4. **Emergency Deployment**: Fast-track deployment with rollback ready
5. **Post-Incident Review**: Comprehensive analysis and prevention measures

## Deliverables
- Root cause analysis with technical explanation
- Robust fix implementation with comprehensive error handling
- Regression test suite to prevent recurrence
- Updated documentation and operational procedures
- Performance impact assessment and optimization
- Monitoring and alerting improvements
- Post-incident report with lessons learned
