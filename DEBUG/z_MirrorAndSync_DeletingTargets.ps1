# First Pass: Copy Files from Source to Destination
function Copy-UpdateFiles {
    param (
        [string]$sourcePath,
        [string]$destPath,
        [bool]$PerformAction = $false
    )

    # Get all files from the source
    $sourceFiles = Get-ChildItem -Path $sourcePath -Recurse -File

    foreach ($sourceFile in $sourceFiles) {
        $destFile = $sourceFile.FullName.Replace($sourcePath, $destPath)

        if (Test-Path $destFile) {
            # File exists in destination, check size
            $sourceSize = (Get-Item $sourceFile.FullName).length
            $destSize = (Get-Item $destFile).length

            if ($sourceSize -ne $destSize) {
                # Copy file if sizes differ
                $message = "Copying file with different sizes (Source: $sourceSize , Destination: $destSize): $destFile"
                Write-Output $message | Out-Host
                if ($PerformAction) {
                    Copy-Item -Path $sourceFile.FullName -Destination $destFile -Force
                }
            }
        } else {
            # Copy missing files
            $message = "Copying new file: $destFile"
            Write-Output $message | Out-Host
            if ($PerformAction) {
                Copy-Item -Path $sourceFile.FullName -Destination $destFile
            }
        }
    }
}

# Second Pass: Remove destination files not present in source
function Remove-ExtraneousFiles {
    param (
        [string]$sourcePath,
        [string]$destPath,
        [bool]$PerformAction = $false
    )

    # Get all files from the destination
    $destFiles = Get-ChildItem -Path $destPath -Recurse -File

    foreach ($destFile in $destFiles) {
        $sourceFile = $destFile.FullName.Replace($destPath, $sourcePath)

        if (-not (Test-Path $sourceFile)) {
            # Remove destination file not present in source
            $message = "Removing destination file not in source: $destFile"
            Write-Output $message | Out-Host
            if ($PerformAction) {
                Remove-Item -Path $destFile.FullName
            }
        }
    }
}

# Third Pass: Update Timestamps
function Update-Timestamps {
    param (
        [string]$sourcePath,
        [string]$destPath,
        [bool]$PerformAction = $false
    )

    # Get all files from the destination
    $destFiles = Get-ChildItem -Path $destPath -Recurse -File

    foreach ($destFile in $destFiles) {
        $sourceFile = $destFile.FullName.Replace($destPath, $sourcePath)

        if (Test-Path $sourceFile) {
            # Update timestamp
            $message = "Updating timestamp for: $destFile"
            Write-Output $message | Out-Host
            if ($PerformAction) {
                $sourceTime = (Get-Item $sourceFile).LastWriteTime
                (Get-Item $destFile.FullName).LastWriteTime = $sourceTime
            }
        }
    }
}

# Function to execute the three main operations
function Execute-MirrorAndSync {
    param (
        [string]$sourcePath,
        [string]$destPath,
        [bool]$PerformAction = $false
    )
    # Ensure that parameters are provided
    if (-not $sourcePath -or -not $destPath) {
        $message = "Error: Source and Destination paths must be provided to 'Execute-MirrorAndSync'"
        Write-Output $message | Out-Host
        return
    }
    
    # Warning message
    $warning = @"
    WARNING: 

    You are about to synchronize files from '$sourcePath' into '$destPath'.
    This operation WILL OVERWRITE existing files where they have different sizes and
    WILL DELETE files in the destination which are not present in the source !

    Final Warning: Do you want to continue with this possibly destuctive action ? (Y/N)
"@
    Write-Output $warning | Out-Host
    $response = Read-Host "Enter Y to continue or N to abort"
    if ($response -ne 'Y' -and $response -ne 'y') {
        Write-Output "Operation aborted by user." | Out-Host
        return
    }
    $message = "Starting file synchronization from '$sourcePath' to '$destPath' with PerformAction=$PerformAction"
    Write-Output $message | Out-Host
    # First Pass: Copy Files from Source to Destination
    Copy-UpdateFiles -sourcePath $sourcePath -destPath $destPath -PerformAction $PerformAction
    # Second Pass: Remove destination files not present in source
    Remove-ExtraneousFiles -sourcePath $sourcePath -destPath $destPath -PerformAction $PerformAction
    # Third Pass: Update Timestamps
    Update-Timestamps -sourcePath $sourcePath -destPath $destPath -PerformAction $PerformAction
    $message = "Synchronization complete."
    Write-Output $message | Out-Host
}

#======================================================================================
# -------------------
$source      = "X:\ROOTFOLDER1\SciFi"
$destination = "V:\ROOTFOLDER2\SciFi"
#Execute-MirrorAndSync -sourcePath $source -destPath $destination -PerformAction $true
Execute-MirrorAndSync -sourcePath $source -destPath $destination -PerformAction $false
# -------------------
# -------------------
$source      = "X:\ROOTFOLDER1\SciFi"
$destination = "F:\ROOTFOLDER3\SciFi"
#Execute-MirrorAndSync -sourcePath $source -destPath $destination -PerformAction $true
Execute-MirrorAndSync -sourcePath $source -destPath $destination -PerformAction $false
# -------------------
# -------------------
$source      = "X:\ROOTFOLDER1\SciFi"
$destination = "H:\ROOTFOLDER4\SciFi"
#Execute-MirrorAndSync -sourcePath $source -destPath $destination -PerformAction $true
Execute-MirrorAndSync -sourcePath $source -destPath $destination -PerformAction $false
# -------------------
# -------------------
$source      = "X:\ROOTFOLDER1\SciFi"
$destination = "K:\ROOTFOLDER5\SciFi"
#Execute-MirrorAndSync -sourcePath $source -destPath $destination -PerformAction $true
Execute-MirrorAndSync -sourcePath $source -destPath $destination -PerformAction $false
# -------------------

#======================================================================================
# DISK 1:
#	X:\ROOTFOLDER1\2015.11.29-Jess-21st-birthday-party
#	X:\ROOTFOLDER1\CharlieWalsh
#	X:\ROOTFOLDER1\ClassicDocumentaries
#	X:\ROOTFOLDER1\ClassicMovies
#	X:\ROOTFOLDER1\Family_Photos
#	X:\ROOTFOLDER1\Footy
#	X:\ROOTFOLDER1\Movies_unsorted
#	X:\ROOTFOLDER1\SciFi
#	
# DISK 2:
#	V:\ROOTFOLDER2\2015.11.29-Jess-21st-birthday-party
#	V:\ROOTFOLDER2\Documentaries
#	V:\ROOTFOLDER2\ClassicMovies
#	V:\ROOTFOLDER2\Family_Photos
#	V:\ROOTFOLDER2\Footy
#	V:\ROOTFOLDER2\HomePics
#	V:\ROOTFOLDER2\Movies
#	V:\ROOTFOLDER2\Movies_unsorted
#	V:\ROOTFOLDER2\SciFi
#
# DISK 3:
#	F:\ROOTFOLDER3\2015.11.29-Jess-21st-birthday-party
#	F:\ROOTFOLDER3\CharlieWalsh
#	F:\ROOTFOLDER3\ClassicDocumentaries
#	F:\ROOTFOLDER3\ClassicMovies
#	F:\ROOTFOLDER3\Family_Photos
#	F:\ROOTFOLDER3\Footy
#	F:\ROOTFOLDER3\Movies
#	F:\ROOTFOLDER3\OldMovies
#	F:\ROOTFOLDER3\SciFi
#
# DISK 4:
#	H:\ROOTFOLDER4\2015.11.29-Jess-21st-birthday-party
#	H:\ROOTFOLDER4\BigIdeas
#	H:\ROOTFOLDER4\CharlieWalsh
#	H:\ROOTFOLDER4\ClassicDocumentaries
#	H:\ROOTFOLDER4\ClassicMovies
#	H:\ROOTFOLDER4\Family_Photos
#	H:\ROOTFOLDER4\Footy
#	H:\ROOTFOLDER4\Movies
#	H:\ROOTFOLDER4\OldMovies
#	H:\ROOTFOLDER4\SciFi
#	H:\ROOTFOLDER4\Series
#
# DISK 5:
#	K:\ROOTFOLDER5\2015.11.29-Jess-21st-birthday-party
#	K:\ROOTFOLDER5\BigIdeas
#	K:\ROOTFOLDER5\CharlieWalsh
#	K:\ROOTFOLDER5\ClassicDocumentaries
#	K:\ROOTFOLDER5\ClassicMovies
#	K:\ROOTFOLDER5\Family_Photos
#	K:\ROOTFOLDER5\Footy
#	K:\ROOTFOLDER5\Movies
#	K:\ROOTFOLDER5\MusicVideos
#	K:\ROOTFOLDER5\OldMovies
#	K:\ROOTFOLDER5\SciFi
#
#======================================================================================
